from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.states.blog_state import ChatState
from src.nodes.blog_node import ChatNode

class GraphBuilder:
    def __init__(self, llm):
        self.llm = llm

    def build_graph(self):
        graph = StateGraph(ChatState)
        chat_node = ChatNode(self.llm)
        graph.add_node("chatbot", chat_node.chatbot)
        graph.add_edge(START, "chatbot")
        graph.add_edge("chatbot", END)
        memory = MemorySaver()
        return graph.compile(checkpointer=memory)
