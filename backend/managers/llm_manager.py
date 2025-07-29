import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()

API_KEY = os.getenv("API_KEY")

llm = ChatOpenAI(
    api_key=API_KEY,
    temperature=0,
    model="gpt-4.1-mini-2025-04-14",
)
