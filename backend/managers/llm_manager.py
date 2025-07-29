import os

from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI


load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

llm = ChatMistralAI(
    api_key=MISTRAL_API_KEY,
    temperature=0,
    model_name ="mistral-large-latest",
)
