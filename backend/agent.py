# -------------------------- Database --------------------------
#

from dotenv import load_dotenv
import os
from logger import log_tool_call, log_tool_result, log_llm_decision, log_llm_response

load_dotenv()

uri = f"sqlite:///Chinook_Sqlite.sqlite"

from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri(uri)

# -------------------------- LLM --------------------------

from langchain_mistralai import ChatMistralAI

API_KEY = os.getenv("API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

llm = ChatMistralAI(
    model="mistral-medium-2505" # type: ignore
)

# -------------------------- Tools --------------------------

from langchain_community.tools import tool


@tool("ListTablesTool")
def list_tables_tool():
    """Use this tool to get all the available table names, to then choose those that might be relevant to the user's question.
    Returns:
        str: The list of the tables available for querying
    """
    log_tool_call("ListTablesTool", {})
    query = f"""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
    """
        # SELECT TABLE_NAME
        # FROM INFORMATION_SCHEMA.TABLES
        # WHERE TABLE_TYPE = 'BASE TABLE'
    results = db.run_no_throw(query)
    if not results:
        log_tool_result("ListTablesTool", "No tables found")
        return f"No tables found."
    log_tool_result("ListTablesTool", results)
    return results


@tool("GetSampleRows")
def get_sample_rows(selected_table):
    """Use this tool once the relevant tables have been selected, to get sample rows the tables.
    This tool takes only one table as argument.
    For several tables, call the tool several times.
    From there, build the query to answer the user's question.

    Args:
        selected_table: Name of a table in the database    Returns:
        str: A few sample rows from the table (including column names)
    """
    log_tool_call("GetSampleRows", {"selected_table": selected_table})
    query = f"""
                SELECT *
                FROM [{selected_table}]
                LIMIT 5
            """

    results = db.run_no_throw(query, include_columns=True)
    log_tool_result("GetSampleRows", results)

    return results


@tool("ExecuteQuery")
def execute_query(sql_statement):
    """Use this tool once you built the query that will retrieve results answering the user's question.
    Beware that this tool has safeguards and will reject your query if it could potentially yield large results.
    Args:
        sql_statement: A correct SQLite SELECT statement that retrieves results answering the user's question
    Returns:
        str: The statement result
    """
    log_tool_call("ExecuteQuery", {"sql_statement": sql_statement})
    stmt_upper = sql_statement.strip().upper()
    # check if it's a SELECT without aggregation or LIMIT clause
    risky = (
        stmt_upper.startswith("SELECT")
        and "LIMIT" not in stmt_upper
        and "COUNT(" not in stmt_upper
        and "SUM(" not in stmt_upper
        and "AVG(" not in stmt_upper
        and "GROUP BY" not in stmt_upper
    )

    # # reject if risky
    # if risky:
    #     result = "Query rejected: potential to return a large number of rows. Please include a LIMIT clause (e.g., SELECT * ... LIMIT 100 ...) or use aggregation."
    #     log_tool_result("ExecuteQuery", result)
    #     return result

    results = db.run_no_throw(sql_statement)
    log_tool_result("ExecuteQuery", results)
    return results


tools = [list_tables_tool, get_sample_rows, execute_query]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

# -------------------------- Helper Functions --------------------------


def log_cost(cb):
    """Helper function to log costs"""
    with open("../cost/cost_history.txt", "a") as f:
        f.write(f"{str(cb)}\n\n")

    latest_cost = cb.total_cost
    with open("../cost/total_cost.txt", "r") as f:
        total_cost = float(f.read().strip())
    total_cost += latest_cost
    with open("../cost/total_cost.txt", "w") as f:
        f.write(f"{total_cost}")


# -------------------------- Workflow --------------------------

from langgraph.graph import add_messages
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
)
from langchain_community.callbacks import get_openai_callback

# -------------------------- Workflow --------------------------

from typing import TypedDict, Annotated, List, NotRequired
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_question: NotRequired[str]
    executed_query: NotRequired[str]
    query_result: NotRequired[str]


def call_llm_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """LLM decides whether to call a tool or not"""
    with get_openai_callback() as cb:
        result = llm_with_tools.invoke(
            [
                SystemMessage(                    content="""You are an expert SQLite assistant that translates natural language questions into business-relevant answers, using SQL under the hood, but without exposing any technical details to the user.
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
                )            ]
            + state["messages"]
        )

    # Log LLM response details
    if hasattr(result, 'tool_calls') and getattr(result, 'tool_calls', None):
        tool_calls = getattr(result, 'tool_calls', [])
        log_llm_decision("LLM_TOOL_DECISION", f"Calling {len(tool_calls)} tool(s): {[tc['name'] for tc in tool_calls]}")
        for tc in tool_calls:
            log_tool_call(tc['name'], tc['args'])
    else:
        log_llm_response(result.content)
    
    return {
        "messages": [result],
    }


def call_tools_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """Execute tool calls from the LLM response"""
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls: # type: ignore
        return state

    tool_results = []
    executed_query = state.get("executed_query", "")
    query_result = state.get("query_result", "")

    for tool_call in last_message.tool_calls: # type: ignore
        tool_name = tool_call["name"]
        tool = tools_by_name[tool_name]
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

    return {"user_question": user_question} # type: ignore


def should_continue_tools(state: AgentState) -> str:
    """Determine if we should continue with tool execution"""
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls: # type: ignore
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
    workflow.add_edge("extract_question", "call_llm")    # Conditional edge after LLM call
    workflow.add_conditional_edges(
        "call_llm",
        should_continue_tools,
        {"call_tools": "call_tools", END: END},
    )

    # After tool execution, go back to LLM
    workflow.add_edge("call_tools", "call_llm")

    return workflow.compile()


graph = create_agent_graph()