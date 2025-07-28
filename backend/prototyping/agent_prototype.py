import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_mistralai import ChatMistralAI
from langchain_community.tools import tool
from langgraph.graph import add_messages, StateGraph, END
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
)
from langchain_community.callbacks import get_openai_callback
from typing import TypedDict, Annotated, List, NotRequired
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig

# -------------------------- Database --------------------------

load_dotenv()

uri = f"sqlite:///real_estate.db"
db = SQLDatabase.from_uri(uri)

# -------------------------- LLM --------------------------

API_KEY = os.getenv("MISTRAL_API_KEY")

llm = ChatMistralAI(model="mistral-small-latest")  # type: ignore

# -------------------------- Tools --------------------------


@tool("ListTablesTool")
def list_tables_tool():
    """Use this tool to get all the available table names, to then choose those that might be relevant to the user's question.
    Returns:
        str: The list of the tables available for querying
    """
    query = f"""
        SELECT name FROM sqlite_master WHERE type='table';
    """
    results = db.run_no_throw(query)
    if not results:
        return f"No tables found."
    return results


@tool("GetSampleRows")
def get_sample_rows(selected_table):
    """Use this tool once the relevant tables have been selected, to get 2 sample rows.
    This tool takes only one table as argument.
    For several tables, call the tool several times.
    From there, build the query to answer the user's question.

    Args:
        selected_table: Name of a table in the database

    Returns:
        str: 2 sample rows from the table (including column names)
    """
    query = f"""
                SELECT *
                FROM [{selected_table}]
                LIMIT 2
            """

    results = db.run_no_throw(query, include_columns=True)

    return results


@tool("ExecuteQuery")
def execute_query(sql_statement):
    """Use this tool once you built the query that will retrieve results answering the user's question.
    Args:
        sql_statement: A correct SQLite SELECT statement that retrieves results answering the user's question
    Returns:
        str: The statement result
    """

    results = db.run_no_throw(sql_statement)
    return results


tools = [list_tables_tool, get_sample_rows, execute_query]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_question: NotRequired[str]
    executed_query: NotRequired[str]
    query_result: NotRequired[str]


def call_llm_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """LLM decides whether to call a tool or not"""
    with get_openai_callback() as cb:
        result = llm_with_tools.invoke([
            SystemMessage(
                content="""You are an expert SQLite assistant. Your job is to translate natural language questions into accurate, business-relevant answers using SQL.

- You can only perform SELECT statements. You are strictly read-only: never write, modify, insert, update, or delete any data, even if the user asks you to. The user can ask you to execute a query, but you must ensure it is a SELECT statement.
- You will be provided with a SQLite database schema and can use tools to query it.
- Always reason step by step:
    1. Identify the user's intent and required information.
    2. List relevant tables and columns.
    3. If needed, request sample rows to understand table structure.
    4. Build a correct SQL SELECT query to answer the question.
    5. Execute the query and present results in a clear, concise format.
- If you need more information, ask clarifying questions or use available tools to inspect the database schema.
- Your answers should be easy to understand for business users, focusing on actionable insights.
"""
            )
        ] + state["messages"])

    return {
        "messages": [result],
    }


def call_tools_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Execute tool calls from the LLM response"""
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:  # type: ignore
        return state

    tool_results = []
    executed_query = state.get("executed_query", "")
    query_result = state.get("query_result", "")

    for tool_call in last_message.tool_calls:  # type: ignore
        tool = tools_by_name[tool_call["name"]]
        result = tool.invoke(tool_call)
        tool_results.append(result)

        if tool_call["name"] == "ExecuteQuery":
            executed_query = tool_call["args"]["sql_statement"]
            query_result = str(result)

    return {
        "messages": tool_results,
        "executed_query": executed_query,
        "query_result": query_result,
    }


def extract_user_question_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Extract and store the user question from the first message"""
    messages = state["messages"]
    user_question = ""
    if messages and isinstance(messages[0], HumanMessage):
        user_question = messages[0].content

    return {"user_question": user_question}  # type: ignore


def should_continue_tools(state: AgentState) -> str:
    """Determine if we should continue with tool execution"""
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:  # type: ignore
        return "call_tools"
    else:
        return END


# Build the graph
def create_agent_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("extract_question", extract_user_question_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("call_tools", call_tools_node)

    # Add edges
    workflow.set_entry_point("extract_question")
    workflow.add_edge("extract_question", "call_llm")  # Conditional edge after LLM call
    workflow.add_conditional_edges(
        "call_llm",
        should_continue_tools,
        {"call_tools": "call_tools", END: END},
    )

    # After tool execution, go back to LLM
    workflow.add_edge("call_tools", "call_llm")

    return workflow.compile()


graph = create_agent_graph()


# Interactive chat loop
def main():
    # ANSI escape codes for color (works in most modern Windows terminals)
    COLOR_RESET = "\033[0m"
    COLOR_USER = "\033[96m"  # Light cyan
    COLOR_AGENT = "\033[92m"  # Light green
    COLOR_QUERY = "\033[93m"  # Yellow
    COLOR_SYSTEM = "\033[95m"  # Magenta
    print(f"{COLOR_SYSTEM}Welcome to the SQLite Agent Demo! Type your questions below. Type 'exit' to quit.{COLOR_RESET}")
    messages = []
    while True:
        user_input = input(f"\n{COLOR_USER}You:{COLOR_RESET} ")
        if user_input.strip().lower() in {"exit", "quit"}:
            print(f"{COLOR_SYSTEM}Goodbye!{COLOR_RESET}")
            break
        messages.append(HumanMessage(content=user_input))
        state = {"messages": messages}
        result = graph.invoke(state)
        if "messages" in result and result["messages"]:
            response = result["messages"][-1].content
            print(f"\n{COLOR_AGENT}Agent:{COLOR_RESET} {response}")
            # Add agent response to history for context
            messages.append(result["messages"][-1])
            if result.get("executed_query"):
                print(f"\n{COLOR_QUERY}--- Executed query ---{COLOR_RESET}\n")
                print(f"{COLOR_QUERY}{result['executed_query']}{COLOR_RESET}")
        else:
            print(result)

if __name__ == "__main__":
    main()
