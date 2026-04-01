from langchain_groq import ChatGroq
import os 
from dotenv import load_dotenv


class GroqLLM:
    def __init__(self):
        load_dotenv()  
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
        )
    
    def get_llm(self):
        return self.llm