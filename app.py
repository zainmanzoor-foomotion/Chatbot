import streamlit as st
import uuid
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.graphs.graph_builder import GraphBuilder
from src.llms.groqllm import GroqLLM

load_dotenv()
os.environ['LANGSMITH_API_KEY'] = os.getenv('LANGSMITH_API_KEY', '')

st.set_page_config(page_title="AI Chatbot", layout="wide")

# --- Init session state ---
if "graph" not in st.session_state:
    llm = GroqLLM().get_llm()
    st.session_state.graph = GraphBuilder(llm).build_graph()

if "threads" not in st.session_state:
    st.session_state.threads = {}  # {thread_id: [{"role": ..., "content": ...}]}

if "current_thread" not in st.session_state:
    tid = str(uuid.uuid4())[:8]
    st.session_state.current_thread = tid
    st.session_state.threads[tid] = []

# --- Sidebar ---
with st.sidebar:
    st.title("Chats")

    if st.button("+ New Chat", use_container_width=True):
        tid = str(uuid.uuid4())[:8]
        st.session_state.current_thread = tid
        st.session_state.threads[tid] = []
        st.rerun()

    st.divider()

    for tid in reversed(list(st.session_state.threads.keys())):
        msgs = st.session_state.threads[tid]
        # Show first user message as label, fallback to thread id
        first_msg = next((m["content"][:30] for m in msgs if m["role"] == "user"), f"Chat {tid}")
        label = f"**{first_msg}**" if tid == st.session_state.current_thread else first_msg
        if st.button(label, key=f"thread_{tid}", use_container_width=True):
            st.session_state.current_thread = tid
            st.rerun()

# --- Main chat area ---
st.title("AI Chatbot")

current_thread = st.session_state.current_thread
messages = st.session_state.threads.get(current_thread, [])

# Display chat history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Type your message..."):
    st.session_state.threads[current_thread].append({"role": "user", "content": prompt})

    # Show user message immediately so it appears above the streaming response
    with st.chat_message("user"):
        st.markdown(prompt)

    config = {"configurable": {"thread_id": current_thread}}

    with st.chat_message("assistant"):
        def token_stream():
            full = ""
            for chunk, _ in st.session_state.graph.stream(
                {"messages": [HumanMessage(content=prompt)]},
                config=config,
                stream_mode="messages"
            ):
                if chunk.content:
                    full += chunk.content
                    yield chunk.content
            st.session_state.threads[current_thread].append({"role": "assistant", "content": full})

        st.write_stream(token_stream())

    st.rerun()
