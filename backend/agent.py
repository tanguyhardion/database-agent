from utils.helpers import update_costs, is_query_risky, can_query_yield_large_results

# -------------------------- Database --------------------------

import ast
import os
import sys

from dotenv import load_dotenv

from utils.logger import (
    log_tool_call,
    log_tool_result,
    log_llm_decision,
    log_llm_response,
)

load_dotenv()

server = os.getenv("DB_SERVER")
db_name = os.getenv("DB_NAME")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = os.getenv("DB_DRIVER")

if not all([server, db_name, username, password, driver]):
    missing = [
        var
        for var, val in {
            "DB_SERVER": server,
            "DB_NAME": db_name,
            "DB_USERNAME": username,
            "DB_PASSWORD": password,
            "DB_DRIVER": driver,
        }.items()
        if not val
    ]

    print(f"Missing environment variables: {', '.join(missing)}. Check the .env file.")
    sys.exit(1)

uri = f"mssql+pyodbc://{username}:{password}@{server}/{db_name}?driver={driver}"

from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri(uri)

# -------------------------- LLM --------------------------

from langchain_mistralai import ChatMistralAI

API_KEY = os.getenv("API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

llm = ChatMistralAI(
    api_key=API_KEY,
    max_tokens=500,
    temperature=0,
    model_name="mistral-large-latest",
)

# -------------------------- Tools --------------------------

from langchain_community.tools import tool


@tool("ListTablesTool")
def list_tables_tool() -> str:
    """Use this tool to get all the available table names, to then choose those that might be relevant to the user's question.
    Returns:
        str: The list of the tables available for querying"""
    query = f"""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            """
            #   AND (
            #     TABLE_SCHEMA = 'refined_zone_operational'
            #     OR TABLE_SCHEMA = 'trusted_zone_metadata'
            #   )
            #   AND (
            #     TABLE_NAME LIKE 'T_MTR_%'
            #     OR
            #     TABLE_NAME LIKE 'T_TRN_%'
            #     OR
            #     TABLE_NAME LIKE 'T_MDS_%'
            #     OR
            #     TABLE_NAME LIKE 'T_MDD_%'
            #   )
    results = db.run_no_throw(query)
    if not results:
        log_tool_result("ListTablesTool", "No tables found")
        return f"No tables found."

    log_tool_result("ListTablesTool", results)
    return results


@tool("GetSampleRows")
def get_sample_rows(selected_table: str) -> str:
    """Use this tool once the relevant tables have been selected, to get sample rows the tables.
    This tool takes only one table as argument.
    For several tables, call the tool several times.
    From there, build the query to answer the user's question.
    One important column definition that is in most tables: TECH_STATUS. Possible values: 0 or 1.
    This column represents whether the corresponding row is active (1) or inactive (0). Always use ACTIVE rows.

    Args:
        selected_table (str): Name of a table in the database
    Returns:
        str: A few sample rows from the table (including column names)
    """
    query = f"""
                SELECT TOP 1 *
                FROM [refined_zone_operational].[{selected_table}]
            """
    if is_query_risky(query):
        results = "Your query has been rejected by the preprocessing script due to a potentially large result set or unsafe statement."
    else:
        results = db.run_no_throw(query, include_columns=True)

    log_tool_result("GetSampleRows", results)

    return results


@tool("GetUniqueColumnValues")
def get_unique_column_values(schema_name: str, table_name: str, column_name: str):
    """
    Retrieve up to 20 unique values for a single TEXT column from a selected table.
    Only one column is supported per call.

    Args:
        schema_name (str): Schema where the table resides.
        table_name (str): Table name.
        column_name (str): Single column name to retrieve unique values for.

    Returns:
        str: A list as a string with up to 20 distinct values from the column, or error message.
    """
    if not column_name or not column_name.isidentifier():
        return "Invalid column name provided."

    col_check_query = f"""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '{schema_name}'
    AND TABLE_NAME = '{table_name}'
    AND COLUMN_NAME = '{column_name}'
    """
    if is_query_risky(col_check_query):
        msg = "A query has been rejected by the preprocessing script due to a potential unsafe statement."
        log_tool_result("GetUniqueColumnValues", msg)
        return msg

    col_info_str = db.run_no_throw(col_check_query)

    try:
        col_info = ast.literal_eval(col_info_str.strip())
    except Exception:
        log_tool_result(
            "GetUniqueColumnValues", f"Failed to parse column info: {col_info_str}"
        )
        return "Failed to retrieve column information."

    if not col_info:
        msg = f"Column '{column_name}' does not exist in {schema_name}.{table_name}."
        log_tool_result("GetUniqueColumnValues", msg)
        return msg

    _, data_type = col_info[0]
    if data_type.lower() not in {"varchar", "nvarchar", "char", "nchar", "text"}:
        msg = f"Column '{column_name}' is not of a TEXT type and cannot be used."
        log_tool_result("GetUniqueColumnValues", msg)
        return msg

    query = (
        f"SELECT DISTINCT TOP 20 [{column_name}] FROM [{schema_name}].[{table_name}]"
    )
    if is_query_risky(query):
        msg = "A query has been rejected by the preprocessing script due to a potential unsafe statement."
        log_tool_result("GetUniqueColumnValues", msg)
        return msg

    col_results_str = db.run_no_throw(query)
    try:
        col_results = ast.literal_eval(col_results_str)
    except Exception:
        log_tool_result(
            "GetUniqueColumnValues", f"Failed to parse query results: {col_results_str}"
        )
        return "Failed to retrieve column values."

    values = [row[column_name] for row in col_results] if col_results else []

    log_tool_result("column_name", values)
    return str(values)


@tool("ExecuteQuery")
def execute_query(query: str) -> str:
    """Use this tool once you built the query that will retrieve results answering the user's question.
    Beware that this tool has safeguards and will reject your query if it could potentially yield large results.
    Beware to use the database's schemas as a prefix to table names, which is:
    - 'refined_zone_operational' for the tables starting with 'T_MTR' or 'T_TRN'

    For example: 'SELECT COUNT(*) FROM refined_zone_operational.T_MTR_COMPANY'

    IMPORTANT:
    This database uses a temporality logic, meaning many tables contain both current and historical data, resulting in possible duplicate records for the same entity (e.g., one record for the present, and others for past states).
    To avoid counting or selecting duplicate entries, you should use the DISTINCT keyword in your SELECT statements wherever appropriate.
    Always consider whether your query might return duplicates due to this temporal structure, and use DISTINCT to ensure your results reflect only unique records relevant to the user's question.
    This is different from the TECH_STATUS=1 filter and it can be paired with it.

    Args:
        query (str): A correct SQL Server SELECT query that retrieves results answering the user's question
    Returns:
        str: The query result
    """
    # - 'trusted_zone_metadata' for the tables starting with 'T_MDS' or 'T_MDD'
    # or 'SELECT COUNT(*) FROM trusted_zone_metadata.T_MDS_ENTITY'
    if is_query_risky(query) or can_query_yield_large_results(query):
        results = "Your query has been rejected by the preprocessing script due to a potentially unsafe statement or large result set."
    else:
        results = db.run_no_throw(query)

    log_tool_result("ExecuteQuery", results)
    return results


tools = [list_tables_tool, get_sample_rows, get_unique_column_values, execute_query]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

# -------------------------- Type definitions --------------------------


from typing import TypedDict, Annotated, List, NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_question: NotRequired[str]
    executed_query: NotRequired[str]
    query_result: NotRequired[str]
    grader_sql_sense: str
    grader_data_sense: str


# -------------------------- Grading --------------------------


from grader import (
    get_sql_sense_grader,
    get_data_sense_grader,
    get_data_hallucination_grader,
    get_answer_relevance_grader,
)


def grade_query_results(state: AgentState, config: RunnableConfig) -> AgentState:
    user_question = state.get("user_question", "")
    query_result = state.get("query_result", "")
    executed_query = state.get("executed_query", "")
    available_tables = list_tables_tool.invoke({})

    if not user_question or not query_result:
        # no data to grade
        return state

    # run graders (simple, sequential, no async for a first try)
    sql_grader = get_sql_sense_grader()
    sense_grader = get_data_sense_grader()

    with get_openai_callback() as cb:
        sql_result = sql_grader.invoke(
            {
                "query": executed_query,
                "question": user_question,
                "available_tables": available_tables,
            }
        )
        sense_result = sense_grader.invoke(
            {"question": user_question, "data_result": query_result}
        )
        update_costs(cb)

    # optionally print or log results (can be adapted to your logger)
    print(f"Grader - SQL sense: {sql_result.binary_score}")
    print(f"Grader - Data sense: {sense_result.binary_score}")

    state["grader_sql_sense"] = sql_result.binary_score
    state["grader_data_sense"] = sense_result.binary_score

    # optionally store results in state for further use
    return {
        **state,
        "grader_sql_sense": sql_result.binary_score,
        "grader_data_sense": sense_result.binary_score,
    }


# -------------------------- Workflow --------------------------

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.callbacks import get_openai_callback
from datetime import datetime


def call_llm_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """LLM decides whether to call a tool or not"""
    with get_openai_callback() as cb:
        result = llm_with_tools.invoke(
            [
                SystemMessage(
                    content=f"""You are an expert SQL Server assistant that translates natural language questions into business-relevant answers, using SQL under the hood, but without exposing any technical details to the user. Business: REAL ESTATE. Adapt your understanding and vocabulary accordingly. FYI, today's date is: {datetime.now().strftime('%Y-%m-%d')}

PRIMARY DIRECTIVE
Never reveal or reference table names, schema names, column names, joins, SQL logic, or any technical detail, even if the user explicitly asks. Treat the user as a business stakeholder. Your job is to deliver accurate, logical, and relevant business answers only. The user should never see how the data is queried or what the structure looks like.

CORE BEHAVIOR
Act like a business analyst using SQL privately to answer business questions.
Provide answers and explanations in plain business language, focused entirely on the insight, not the mechanics of how it was obtained.
Avoid all technical or structural language: no mention of "queries", "columns", "joins", "schemas", or any SQL-related terminology.

REASONING PROTOCOL
Think logically before writing a query: what information would a human analyst need to get this answer?
Use tools like ListTablesTool, GetSampleRows and GetUniqueColumnValues to explore the database privately so as to correctly write, execute and run queries, this is for your internal use only, never mention these tools or what they show.
Only proceed when you have evidence the data can answer the question. Don't guess. Don't fabricate logic.
After executing a query, interpret the results and answer the business question in clear, non-technical terms.
Whatever the result is, explain it logically in business terms, not technically.

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

        update_costs(cb)

    # Log LLM response details
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
        tool_name = tool_call["name"]
        tool = tools_by_name[tool_name]
        result = tool.invoke(tool_call)
        tool_results.append(result)

        if tool_call["name"] == "ExecuteQuery":
            executed_query = tool_call["args"]["query"]
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


def create_agent_graph():
    workflow = StateGraph(AgentState)

    # nodes
    workflow.add_node("extract_question", extract_user_question_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("call_tools", call_tools_node)
    workflow.add_node("grade_query", grade_query_results)

    # edges
    workflow.set_entry_point("extract_question")
    workflow.add_edge("extract_question", "call_llm")

    # conditional edge after LLM call
    workflow.add_conditional_edges(
        "call_llm",
        should_continue_tools,
        {"call_tools": "call_tools", END: END},
    )

    # after tool execution, go to grading
    workflow.add_edge("call_tools", "grade_query")
    # after grading, go back to LLM
    workflow.add_edge("grade_query", "call_llm")

    return workflow.compile()


graph = create_agent_graph()
