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

if "regen_index" not in st.session_state:
    st.session_state.regen_index = None

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

# Capture input early so it renders disabled immediately during streaming
_user_input = st.chat_input(
    "Type your message...",
    disabled=st.session_state.is_responding
)

if st.session_state.pending_error:
    st.error(st.session_state.pending_error)
    st.session_state.pending_error = None

current_thread = st.session_state.current_thread
messages = st.session_state.threads.get(current_thread, [])
regen_idx = st.session_state.regen_index

# When a regen is actively streaming, split display around the streaming slot
is_regen_streaming = (
    st.session_state.pending_prompt is not None and
    st.session_state.is_responding and
    regen_idx is not None
)
split = regen_idx if is_regen_streaming else len(messages)

def render_message_block(msg_slice, index_offset=0):
    import json as _json
    for i, msg in enumerate(msg_slice, start=index_offset):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
        if msg["role"] == "assistant":
            user_msg = next(
                (messages[j]["content"] for j in range(i - 1, -1, -1) if messages[j]["role"] == "user"),
                None
            )
            text_json = _json.dumps(msg["content"])
            st.components.v1.html(f"""
            <div style="display:flex;gap:8px;align-items:center;">
                <button id="copy_{i}" style="display:flex;align-items:center;gap:5px;background:none;border:1px solid #444;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:12px;color:#ccc;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                </button>
            </div>
            <script>
                var btn = document.getElementById("copy_{i}");
                var txt = {text_json};
                btn.addEventListener("click", function() {{
                    navigator.clipboard.writeText(txt).then(function() {{
                        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Copied!';
                        btn.style.color = "#4caf50";
                        btn.style.borderColor = "#4caf50";
                        setTimeout(function() {{
                            btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
                            btn.style.color = "#ccc";
                            btn.style.borderColor = "#444";
                        }}, 2000);
                    }});
                }});
            </script>
            """, height=40)
            if user_msg:
                if st.button("↻ Regenerate", key=f"regen_{i}", disabled=st.session_state.is_responding):
                    st.session_state.threads[current_thread] = messages[:i] + messages[i+1:]
                    st.session_state.pending_prompt = user_msg
                    st.session_state.regen_index = i
                    st.session_state.is_responding = True
                    st.rerun()

# Messages before the streaming slot (or all messages when not regenerating)
render_message_block(messages[:split])

# --- Stream response for pending prompt ---
if st.session_state.pending_prompt and st.session_state.is_responding:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    config = {"configurable": {"thread_id": current_thread}}

    with st.chat_message("assistant"):
        status = st.empty()
        status.caption("Regenerating..." if is_regen_streaming else "Thinking...")

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
                    idx = st.session_state.regen_index
                    if idx is not None:
                        st.session_state.threads[current_thread].insert(idx, {"role": "assistant", "content": full})
                        st.session_state.regen_index = None
                    else:
                        st.session_state.threads[current_thread].append({"role": "assistant", "content": full})
                st.session_state.is_responding = False

        try:
            st.write_stream(token_stream())
        except Exception as e:
            status.empty()
            st.error(f"⚠️ Unexpected error: {e}")
        finally:
            st.session_state.is_responding = False
            st.session_state.pending_prompt = None

    st.rerun()

# Messages after the streaming slot (only shown during regen streaming)
if is_regen_streaming:
    render_message_block(messages[split:], index_offset=split)

# --- Chat input handler ---
if _user_input and not st.session_state.is_responding:
    st.session_state.threads[current_thread].append({"role": "user", "content": _user_input})
    st.session_state.pending_prompt = _user_input
    st.session_state.is_responding = True
    st.rerun()