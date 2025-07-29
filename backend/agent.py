from datetime import datetime
import os
from typing import Annotated, List, NotRequired, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_community.callbacks import get_openai_callback
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from graders.grader import get_sql_sense_grader
from managers.llm_manager import llm
from tools.db_tools import (
    execute_query,
    get_sample_rows,
    get_unique_column_values,
    list_tables_tool,
)
from utils.logger import log_llm_decision, log_llm_response, log_other, log_tool_call


# -------------------------- Tools --------------------------


tools = [
    list_tables_tool,
    get_sample_rows,
    get_unique_column_values,
    execute_query,
]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)


# -------------------------- Type definitions --------------------------


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_question: NotRequired[str]
    executed_query: NotRequired[str]
    query_result: NotRequired[str]
    grader_sql_sense: NotRequired[str]
    grader_data_sense: NotRequired[str]
    retry_count: NotRequired[int]
    grading_feedback: NotRequired[str]
    query_ready_for_grading: NotRequired[bool]


# -------------------------- Grading --------------------------


GRADER_FEEDBACK_PROMPTS = {
    "grader_sql_sense": """The query you executed doesn't make logical sense for the business question asked. Please reconsider your approach and ensure your query methodology aligns with what would actually answer the user's question. Focus on using the right data sources and logic that would provide meaningful business insights.""",
    "grader_data_sense": """The data results you obtained don't provide a sensible answer to the user's question. The numbers or information don't logically address what was asked. Please review your approach and ensure the data you're retrieving actually answers the business question posed.""",
}


def grade_results(state: AgentState, config: RunnableConfig) -> AgentState:
    user_question = state.get("user_question", "")
    query_result = state.get("query_result", "")
    executed_query = state.get("executed_query", "")
    available_tables = list_tables_tool.invoke({})
    retry_count = state.get("retry_count", 0)

    if not user_question or not query_result:
        return state

    log_other(f"Starting grading - Current retry count: {retry_count}")

    # Define graders in order of execution
    graders = [
        (
            "grader_sql_sense",
            get_sql_sense_grader(),
            {
                "query": executed_query,
                "question": user_question,
                "available_tables": available_tables,
            },
        ),
        # Uncomment when ready to use data sense grader
        # (
        #     "grader_data_sense",
        #     get_data_sense_grader(),
        #     {
        #         "question": user_question,
        #         "data_result": query_result,
        #     },
        # ),
    ]

    # Execute graders in order, stop at first failure
    for name, grader, args in graders:
        with get_openai_callback() as cb:
            result = grader.invoke(args)
            grade_result = result.binary_score
            log_other(f"{name}: {grade_result}")

            # If grader fails, provide feedback
            if grade_result == "no":
                state[name] = grade_result

                if retry_count >= 3:
                    # Max retries reached, clear feedback and allow final response
                    log_other(
                        f"Max retries ({retry_count}) reached, allowing final response"
                    )
                    state["grading_feedback"] = ""
                    state["query_ready_for_grading"] = False
                    return state
                else:
                    feedback = GRADER_FEEDBACK_PROMPTS.get(
                        name, "Please reconsider your approach and try again."
                    )
                    new_retry_count = retry_count + 1
                    log_other(
                        f"Grading failed, setting retry count to {new_retry_count} and feedback: {feedback[:50]}..."
                    )

                    # Return updated state with feedback for retry
                    return {
                        **state,
                        name: grade_result,
                        "grading_feedback": feedback,
                        "retry_count": new_retry_count,
                        "query_ready_for_grading": False,
                    }

            # If grader passes, store result and continue
            state[name] = grade_result

    # All graders passed, clear any previous feedback
    log_other("All graders passed, clearing feedback")
    return {
        **state,
        "grading_feedback": "",
        "query_ready_for_grading": False,
    }


# -------------------------- Workflow --------------------------


def call_llm_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """LLM decides whether to call a tool or not"""
    # check if we have grading feedback to provide
    grading_feedback = state.get("grading_feedback", "")

    # get the active prompt and set it as the system message
    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "./system_prompts")
    with open(f"{PROMPTS_DIR}/active.txt", encoding="utf-8") as f:
        prompt_name = f.read()
    with open(f"{PROMPTS_DIR}/{prompt_name}.md", encoding="utf-8") as f:
        template = f.read()
    system_content = template.format(today=datetime.now().strftime("%Y-%m-%d"))

    # add grading feedback if present
    if grading_feedback:
        system_content += f"\n\nIMPORTANT FEEDBACK: {grading_feedback}"

    messages = [SystemMessage(content=system_content)] + state["messages"]

    with get_openai_callback() as cb:
        result = llm_with_tools.invoke(messages)

    # log LLM response details
    if hasattr(result, "tool_calls") and getattr(result, "tool_calls", None):
        tool_calls = getattr(result, "tool_calls", [])
        log_llm_decision(
            "LLM_TOOL_DECISION",
            f"Calling {len(tool_calls)} tool(s): {[tc['name'] for tc in tool_calls]}",
        )
        for tc in tool_calls:
            log_tool_call(tc["name"], tc["args"])
    else:
        log_llm_response(result.content)

    return {
        **state,
        "messages": state["messages"] + [result],
    }


def call_tools_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Execute tool calls from the LLM response"""
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return state

    tool_results = []
    executed_query = state.get("executed_query", "")
    query_result = state.get("query_result", "")
    query_ready_for_grading = False

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool = tools_by_name[tool_name]
        result = tool.invoke(tool_call)
        tool_results.append(result)

        # CRITICAL: Set flag when ExecuteQuery is called
        if tool_call["name"] == "ExecuteQuery":
            args = tool_call.get("args", {})
            executed_query = args.get("query", "")
            query_result = str(result)
            query_ready_for_grading = True

    return {
        **state,
        "messages": state["messages"] + tool_results,
        "executed_query": executed_query,
        "query_result": query_result,
        "query_ready_for_grading": query_ready_for_grading,
    }


def extract_user_question_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Extract and store the user question from the first message"""
    messages = state["messages"]
    user_question = ""
    if messages and isinstance(messages[0], HumanMessage):
        user_question = messages[0].content

    return {"user_question": user_question}


def should_continue_tools(state: AgentState) -> str:
    """Determine if we should continue with tool execution"""
    last_message = state["messages"][-1]

    # If LLM wants to call tools, do it
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "call_tools"
    else:
        # LLM provided a response without tool calls - end the conversation
        return END


def should_continue_after_tools(state: AgentState) -> str:
    """Determine next step after tool execution"""
    # Check if we just executed a query and need grading
    if state.get("query_ready_for_grading", False):
        return "grade_results"
    else:
        # Continue with LLM for more tool calls or final response
        return "call_llm"


def should_continue_after_grading(state: AgentState) -> str:
    """Determine if we should continue after grading"""
    grading_feedback = state.get("grading_feedback", "")
    retry_count = state.get("retry_count", 0)

    log_other(
        f"After grading decision - Feedback: '{grading_feedback}', Retry count: {retry_count}"
    )

    if grading_feedback and retry_count <= 3:
        # Failed grading with retries left - go back to LLM with feedback
        log_other("Going back to LLM with feedback for retry")
        return "call_llm"
    else:
        # Either passed grading or max retries reached - let LLM formulate final response
        log_other("Proceeding to final response")
        return "call_llm"


def create_agent_graph():
    workflow = StateGraph(AgentState)

    # ------------- nodes -------------
    workflow.add_node("extract_question", extract_user_question_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("call_tools", call_tools_node)
    # workflow.add_node("grade_results", grade_results)

    # ------------- edges -------------

    # Start by extracting the user question from the initial message
    workflow.add_edge(START, "extract_question")

    # Once the question is extracted, the LLM decides the next action
    workflow.add_edge("extract_question", "call_llm")

    # Based on the LLM output, decide whether to call tools or end the workflow
    workflow.add_conditional_edges(
        "call_llm",
        should_continue_tools,
        {
            "call_tools": "call_tools",  # If tools are needed, call them
            END: END,  # Otherwise, terminate the workflow
        },
    )

    # CRITICAL: After tools are called, skip grading and always continue with LLM
    workflow.add_edge("call_tools", "call_llm")

    # Grading is disabled, so this edge is not needed

    return workflow.compile()


graph = create_agent_graph()
