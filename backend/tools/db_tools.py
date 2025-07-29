import ast

from langchain_community.tools import tool

from managers.db_manager import db
from utils.helpers import is_query_risky, can_query_yield_large_results
from utils.logger import log_tool_result


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
        FROM {selected_table}
        LIMIT 2
    """

    results = db.run_no_throw(query, include_columns=True)

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
    PRAGMA table_info({table_name});
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

    # PRAGMA table_info returns list of tuples: (cid, name, type, notnull, dflt_value, pk)
    col_details = [col for col in col_info if col[1] == column_name]
    if not col_details:
        msg = f"Column '{column_name}' does not exist in {table_name}."
        log_tool_result("GetUniqueColumnValues", msg)
        return msg

    data_type = col_details[0][2]
    if data_type.lower() not in {"varchar", "nvarchar", "char", "nchar", "text", "string"}:
        msg = f"Column '{column_name}' is not of a TEXT type and cannot be used."
        log_tool_result("GetUniqueColumnValues", msg)
        return msg

    query = (
        f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT 20"
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

    values = [row[0] for row in col_results] if col_results else []

    log_tool_result("column_name", values)
    return str(values)


@tool("ExecuteQuery")
def execute_query(sql_statement):
    """Use this tool once you built the query that will retrieve results answering the user's question.
    Args:
        sql_statement: A correct SQLite SELECT statement that retrieves results answering the user's question
    Returns:
        str: The statement result
    """
    # Beware that this tool has safeguards and will reject your query if it could potentially yield large results.
    stmt_upper = sql_statement.strip().upper()
    # check if it's a SELECT without aggregation or TOP clause
    # risky = (
    #     stmt_upper.startswith("SELECT")
    #     and "LIMIT" not in stmt_upper
    #     and "COUNT(" not in stmt_upper
    #     and "SUM(" not in stmt_upper
    #     and "AVG(" not in stmt_upper
    #     and "GROUP BY" not in stmt_upper
    # )

    # # reject if risky
    # if risky:
    #     return (
    #         "Query rejected: potential to return a large number of rows. "
    #         "Please include a LIMIT clause (e.g., SELECT * ... LIMIT 100 ...) or use aggregation."
    #     )

    results = db.run_no_throw(sql_statement)
    return results
