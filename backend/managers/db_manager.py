from langchain_community.utilities import SQLDatabase


uri = f"sqlite:///database/real_estate.db"

db = SQLDatabase.from_uri(uri)
