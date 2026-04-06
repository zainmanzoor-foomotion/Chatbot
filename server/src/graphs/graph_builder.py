from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from src.states.state import ChatState
from src.nodes.node import ChatNode
from src.tools.tools import tools


class GraphBuilder:
    def __init__(self, llm):
        self.llm = llm

    def build_graph(self):
        chat_node = ChatNode(self.llm, tools)

        graph = StateGraph(ChatState)

        graph.add_node("ModelTool", chat_node.model_tool)
        graph.add_node("tools", ToolNode(tools))

        graph.add_edge(START, "ModelTool")

        # If the LLM made tool calls → go to tools node, otherwise → END
        graph.add_conditional_edges("ModelTool", tools_condition)

        # After tools execute, loop back to LLM so it can process results
        graph.add_edge("tools", "ModelTool")

        memory = MemorySaver()
        return graph.compile(checkpointer=memory)
