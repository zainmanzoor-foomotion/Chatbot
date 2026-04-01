import streamlit as st
import uuid
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from src.graphs.graph_builder import GraphBuilder
from src.llms.groqllm import GroqLLM

load_dotenv()
os.environ['LANGSMITH_API_KEY'] = os.getenv('LANGSMITH_API_KEY', '')

st.set_page_config(page_title="AI Chatbot", layout="wide")

st.html("<script>window.parent.document.querySelector('section.main').scrollTo(0, window.parent.document.querySelector('section.main').scrollHeight);</script>")

# --- Init session state ---
if "graph" not in st.session_state:
    llm = GroqLLM().get_llm()
    st.session_state.graph = GraphBuilder(llm).build_graph()

if "threads" not in st.session_state:
    st.session_state.threads = {}

if "pending_error" not in st.session_state:
    st.session_state.pending_error = None

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "is_responding" not in st.session_state:
    st.session_state.is_responding = False

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
        first_msg = next((m["content"][:30] for m in msgs if m["role"] == "user"), f"Chat {tid}")
        label = f"**{first_msg}**" if tid == st.session_state.current_thread else first_msg
        if st.button(label, key=f"thread_{tid}", use_container_width=True):
            st.session_state.current_thread = tid
            st.rerun()

# --- Main chat area ---
st.title("AI Chatbot")

if st.session_state.pending_error:
    st.error(st.session_state.pending_error)
    st.session_state.pending_error = None

current_thread = st.session_state.current_thread
messages = st.session_state.threads.get(current_thread, [])

# Display chat history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat input (disabled while responding) ---
if prompt := st.chat_input(
    "Type your message...",
    disabled=st.session_state.is_responding
):
    st.session_state.threads[current_thread].append({"role": "user", "content": prompt})
    st.session_state.pending_prompt = prompt
    st.session_state.is_responding = True
    st.rerun()  # Rerun immediately so input disables before streaming starts

# --- Stream response for pending prompt ---
if st.session_state.pending_prompt and st.session_state.is_responding:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    config = {"configurable": {"thread_id": current_thread}}

    with st.chat_message("assistant"):
        status = st.empty()
        status.caption("Thinking...")

        def token_stream():
            full = ""
            first_token = True
            tools_used = []
            try:
                for chunk, metadata in st.session_state.graph.stream(
                    {"messages": [HumanMessage(content=prompt)]},
                    config=config,
                    stream_mode="messages"
                ):
                    if isinstance(chunk, ToolMessage):
                        tool_name = getattr(chunk, "name", "tool")
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
                        tools_list = ", ".join(f"`{t}`" for t in tools_used)
                        status.caption(f"Using tools: {tools_list}...")
                        continue

                    has_tool_calls = bool(getattr(chunk, "tool_calls", [])) or \
                                     bool(getattr(chunk, "tool_call_chunks", []))
                    if has_tool_calls:
                        continue

                    if isinstance(chunk, (AIMessageChunk, AIMessage)) and chunk.content:
                        if first_token:
                            status.empty()
                            first_token = False
                        full += chunk.content
                        yield chunk.content

            except Exception as e:
                err = str(e)
                status.empty()
                if "INVALID_CHAT_HISTORY" in err or "tool_calls" in err:
                    new_tid = str(uuid.uuid4())[:8]
                    st.session_state.threads[new_tid] = []
                    st.session_state.current_thread = new_tid
                    full = "⚠️ Session history was corrupted. A new chat has been started — please resend your message."
                else:
                    full = f"⚠️ {err}"
                yield full

            finally:
                status.empty()
                if full:
                    st.session_state.threads[current_thread].append({"role": "assistant", "content": full})
                # Always unlock, even if response was empty
                st.session_state.is_responding = False

        # Outer safety net in case write_stream itself throws
        try:
            st.write_stream(token_stream())
        except Exception as e:
            status.empty()
            st.error(f"⚠️ Unexpected error: {e}")
        finally:
            # Guaranteed unlock no matter what
            st.session_state.is_responding = False
            st.session_state.pending_prompt = None

    st.rerun()