from src.states.blog_state import ChatState
from langchain_core.messages import SystemMessage

SYSTEM_PROMPT = """You are a professional AI assistant. Follow these guidelines in every response:
- Be clear, concise, and accurate.
- Use proper formatting (headings, bullet points, code blocks) where appropriate.
- Maintain a professional and helpful tone at all times.
- If you are unsure about something, say so honestly rather than guessing."""

class ChatNode:
    """Chatbot node"""
    def __init__(self, llm):
        self.llm = llm

    def chatbot(self, state: ChatState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state['messages'])
        response = self.llm.invoke(messages)
        return {"messages": [response]}
