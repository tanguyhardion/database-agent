import logging
from datetime import datetime

# Configure simple file logging for LLM model activity only
logging.basicConfig(
    filename='llm_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filemode='a'
)

logger = logging.getLogger('llm_model')

def log_llm_decision(decision_type, details):
    """Log LLM decisions and actions"""
    logger.info(f"{decision_type}: {details}")

def log_tool_call(tool_name, args):
    """Log tool calls made by LLM"""
    logger.info(f"TOOL_CALL: {tool_name} with args: {args}")

def log_tool_result(tool_name, result):
    """Log results from tool executions"""
    result_str = str(result)[:500]  # Limit to 500 chars
    logger.info(f"TOOL_RESULT: {tool_name} returned: {result_str}")

def log_llm_response(response):
    """Log final LLM response"""
    response_str = str(response)[:500]  # Limit to 500 chars
    logger.info(f"LLM_RESPONSE: {response_str}")
