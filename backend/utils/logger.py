import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Create a log file per day using date
date_str = datetime.now().strftime("%Y%m%d")
log_filename = f"llm_activity_{date_str}.log"

# Configure simple file logging for LLM model activity only
logging.basicConfig(
    filename=os.path.join(logs_dir, log_filename),
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filemode="a",
)

logger = logging.getLogger("llm_model")


def log_llm_decision(decision_type, details):
    """Log LLM decisions and actions"""
    logger.info(f"{decision_type}: {details}")


def log_tool_call(tool_name, args):
    """Log tool calls made by LLM"""
    logger.info(f"TOOL_CALL: {tool_name} with args: {args}")


def log_tool_result(tool_name, result):
    """Log results from tool executions"""
    result_str = str(result)
    logger.info(f"TOOL_RESULT: {tool_name} returned: {result_str}")


def log_llm_response(response):
    """Log final LLM response"""
    response_str = str(response)
    logger.info(f"LLM_RESPONSE: {response_str}")

def log_other(message):
    """Log other messages or events"""
    logger.info(f"OTHER: {message}")