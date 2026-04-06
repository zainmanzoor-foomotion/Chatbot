from langchain_groq import ChatGroq
import os 
from dotenv import load_dotenv


DEFAULT_MODEL = "openai/gpt-oss-20b"

class GroqLLM:
    def __init__(self, model: str = DEFAULT_MODEL):
        load_dotenv()
        self.llm = ChatGroq(
            model=model,
            api_key=os.getenv("GROQ_API_KEY"),
        )

    def get_llm(self):
        return self.llm