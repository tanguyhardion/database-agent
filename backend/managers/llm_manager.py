import os

from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI


load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

llm = ChatMistralAI(
    api_key=MISTRAL_API_KEY,
    temperature=0,
)
