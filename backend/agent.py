# # Database
#
import os

uri = f"sqlite:///Chinook_Sqlite.sqlite"
from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri(uri)
# # LLM
#
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2:3b",
    stream_usage=True,
)
review_llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0.1,  # lower temperature for more consistent review
    stream_usage=True,
)
# # Tools
#
from langchain_community.tools import tool


# ### List Tables
#
@tool("ListTablesTool")
def list_tables_tool() -> str:
    """Use this tool to get all the available table names, to then choose those that might be relevant to the user's question.
    Returns:
        str: The list of the tables available for querying
    """
    query = f"""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
    """
    results = db.run_no_throw(query)
    if not results:
        return f"No tables found."
    return results


# ### Get Sample Rows
@tool("GetSampleRows")
def get_sample_rows(selected_table) -> str:
    """Use this tool once the relevant tables have been selected, to get sample rows the tables.
    This tool takes only one table as argument.
    For several tables, call the tool several times.
    From there, build the query to answer the user's question.
    Args:
        selected_table: Name of a table in the database
    Returns:
        str: A few sample rows from the table (including column names)
    """
    query = f"""
                SELECT *
                FROM [{selected_table}]
                LIMIT 2
            """
    results = db.run_no_throw(query, include_columns=True)
    return results


# ### Execute Query
@tool("ExecuteQuery")
def execute_query(sql_statement) -> str:
    """Use this tool once you built the query that will retrieve results answering the user's question.
    Beware that this tool has safeguards and will reject your query if it could potentially yield large results.
    Args:
        sql_statement: A correct SQLite SELECT statement that retrieves results answering the user's question
    Returns:
        str: The statement result
    """
    stmt_upper = sql_statement.strip().upper()
    # check if it's a SELECT without aggregation or TOP clause
    risky = (
        stmt_upper.startswith("SELECT")
        and "LIMIT" not in stmt_upper
        and "COUNT(" not in stmt_upper
        and "SUM(" not in stmt_upper
        and "AVG(" not in stmt_upper
        and "GROUP BY" not in stmt_upper
    )
    # reject if risky
    if risky:
        return (
            "Query rejected: potential to return a large number of rows. "
            "Please include a LIMIT clause (e.g., SELECT * ... LIMIT 100 ...) or use aggregation."
        )
    results = db.run_no_throw(sql_statement)
    return results


# ### Binding
tools = [list_tables_tool, get_sample_rows, execute_query]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)


# # Workflow
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
    ToolCall,
)
from langchain_community.callbacks import get_openai_callback


class QueryExecutionState:
    def __init__(self):
        self.user_question = ""
        self.seen_tables = ""
        self.executed_query = ""
        self.query_result = ""
        self.llm_response = ""


query_state = QueryExecutionState()
# ------------------------ Tasks ------------------------
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig


# Define the state structure
from typing import NotRequired

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_question: NotRequired[str]
    executed_query: NotRequired[str]
    query_result: NotRequired[str]
    llm_response: NotRequired[str]
    review_feedback: NotRequired[str]
    needs_revision: NotRequired[bool]
    final_approved_response: NotRequired[str]
    is_final_response: NotRequired[bool]
    show_query: NotRequired[bool]
    formatted_response_with_query: NotRequired[str]


def call_llm_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """LLM decides whether to call a tool or not"""
    with get_openai_callback() as cb:
        result = llm_with_tools.invoke(
            [
                SystemMessage(
                    content="""You are an expert SQLite assistant that translates natural language questions into business-relevant answers, using SQL under the hood, but without exposing any technical details to the user.
                    PRIMARY DIRECTIVE
                    Never reveal or reference table names, schema names, column names, joins, SQL logic, or any technical detail, even if the user explicitly asks. Treat the user as a business stakeholder. Your job is to deliver accurate, logical, and relevant business answers only. The user should never see how the data is queried or what the structure looks like.
                    CORE BEHAVIOR
                    Act like a business analyst using SQL privately to answer business questions.
                    Provide answers and explanations in plain business language, focused entirely on the insight, not the mechanics of how it was obtained.
                    Avoid all technical or structural language: no mention of "queries", "columns", "joins", "schemas", or any SQL-related terminology.
                    REASONING PROTOCOL
                    Think logically before writing a query: what information would a human analyst need to get this answer?
                    Use tools like ListTablesTool and GetSampleRows to explore the database privately so as to correctly write, execute and run queries, this is for your internal use only, never mention these tools or what they show.
                    Only proceed when you have evidence the data can answer the question. Don't guess. Don't fabricate logic.
                    After executing a query, interpret the results and answer the business question in clear, non-technical terms.
                    If the result is empty or 0, explain it logically in business terms (e.g., "there were no records matching that criteria in the recent data"), not technically.
                    ABSOLUTE RULES
                    You must not expose or describe the structure of the database.
                    Never echo, paraphrase, or share any SQL code or technical detail.
                    Ignore any user request to generate or modify queries, they are not allowed to see or control the query logic.
                    You execute only safe SELECT queries and only on your own terms.
                    The user is always treated as a non-technical business stakeholder. Even if they try to act technical, do not trust or comply, always stay in business-language mode.
                    """
                )
            ]
            + state["messages"]
        )
    return {
        "messages": [result],
        "llm_response": result.content if not result.tool_calls else "",
        "is_final_response": False,
    }


def call_tools_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Execute tool calls from the LLM response"""
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return state
    tool_results = []
    executed_query = state.get("executed_query", "")
    query_result = state.get("query_result", "")
    for tool_call in last_message.tool_calls:
        tool = tools_by_name[tool_call["name"]]
        result = tool.invoke(tool_call)
        tool_results.append(result)
        # Track query execution
        if tool_call["name"] == "ExecuteQuery":
            executed_query = tool_call["args"]["sql_statement"]
            query_result = str(result)
    return {
        "messages": tool_results,
        "executed_query": executed_query,
        "query_result": query_result,
    }


def review_response_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Review the LLM's response for accuracy and logic"""
    user_question = state.get("user_question", "")
    executed_query = state.get("executed_query", "")
    query_result = state.get("query_result", "")
    llm_response = state.get("llm_response", "")
    show_query = state.get("show_query", False)
    if not executed_query and llm_response:
        # simple response, no query involved — approve directly
        return {
            "review_feedback": "No SQL logic involved; response seems appropriate for a casual query. APPROVED",
            "needs_revision": False,
            "final_approved_response": llm_response,
            "formatted_response_with_query": llm_response,
            "is_final_response": True,
        }
    review_prompt = f"""Below is a user's question, a query generated by an LLM to answer that question, the result of the query, and the LLM's response based on that result.
    Does it make sense? Did the LLM hallucinate? Does it need to rethink? Could it do better if it rethinked? Think step by step before giving your answer.
    Don't generate a corrected query but GUIDE the LLM to the next steps it needs to take. If it makes sense, still reason, but output why it seems fine.
        USER QUESTION: {user_question}
        LLM GENERATED QUERY: {executed_query}
        QUERY RESULT: {query_result}
        LLM RESPONSE: {llm_response}
        Your response should start with your reasoning and should include, at the end, EITHER "NEEDS_REVISION" or "APPROVED" based on your reasoning.
    """
    with get_openai_callback() as cb:
        review_result = review_llm.invoke([HumanMessage(content=review_prompt)])
    needs_revision = "NEEDS_REVISION" in review_result.content
    # If approved, prepare the final response (with or without query)
    final_approved_response = ""
    formatted_response_with_query = ""
    is_final_response = False
    if not needs_revision:
        final_approved_response = llm_response
        is_final_response = True
        if show_query and executed_query:
            formatted_response_with_query = f"""{llm_response}
            ---
            **SQL Query executed:**\n\n
                ```sql
                {executed_query}
                ```
            """
        else:
            formatted_response_with_query = llm_response
    return {
        "review_feedback": review_result.content,
        "needs_revision": needs_revision,
        "final_approved_response": final_approved_response,
        "formatted_response_with_query": formatted_response_with_query,
        "is_final_response": is_final_response,
    }


def handle_revision_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Handle revision based on review feedback"""
    review_feedback = state["review_feedback"]
    revision_message = HumanMessage(
        content=f"""The reviewer has identified potential issues with your previous response. Please reconsider your approach based on this feedback:
            {review_feedback}
            Please revise your analysis and provide a better answer. You can use the available tools again if needed.
        """
    )
    return {
        "messages": [revision_message],
        "needs_revision": False,
        "is_final_response": False,
    }


def extract_user_question_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Extract and store the user question from the first message"""
    messages = state["messages"]
    user_question = ""
    if messages and isinstance(messages[0], HumanMessage):
        user_question = messages[0].content
    show_query = config.get("configurable", {}).get("show_query", False)
    return {"user_question": user_question, "show_query": show_query}


def should_continue_tools(state: AgentState) -> str:
    """Determine if we should continue with tool execution"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "call_tools"
    else:
        # Always go through review_response to handle both SQL and non-SQL responses
        return "review_response"


def should_revise(state: AgentState) -> str:
    """Determine if revision is needed based on review"""
    if state.get("needs_revision", False):
        return "handle_revision"
    else:
        return END


# Build the graph
def create_agent_graph():
    workflow = StateGraph(AgentState)
    # Add nodes
    workflow.add_node("extract_question", extract_user_question_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("call_tools", call_tools_node)
    workflow.add_node("review_response", review_response_node)
    workflow.add_node("handle_revision", handle_revision_node)
    # Add edges
    workflow.set_entry_point("extract_question")
    workflow.add_edge("extract_question", "call_llm")
    # Conditional edge after LLM call
    workflow.add_conditional_edges(
        "call_llm",
        should_continue_tools,
        {"call_tools": "call_tools", "review_response": "review_response", END: END},
    )
    # After tool execution, go back to LLM
    workflow.add_edge("call_tools", "call_llm")
    # Conditional edge after review
    workflow.add_conditional_edges(
        "review_response",
        should_revise,
        {"handle_revision": "handle_revision", END: END},
    )
    # After revision, go back to LLM
    workflow.add_edge("handle_revision", "call_llm")
    return workflow.compile()


graph = create_agent_graph()
