import uvicorn
import uuid
import os
import json
import asyncio
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from src.graphs.graph_builder import GraphBuilder
from src.llms.groqllm import GroqLLM

load_dotenv()
os.environ['LANGSMITH_API_KEY'] = os.getenv('LANGSMITH_API_KEY', '')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Build one graph per supported model at startup ---
SUPPORTED_MODELS = ["openai/gpt-oss-20b", "qwen/qwen3-32b","llama-3.3-70b-versatile"]

graphs = {
    model_id: GraphBuilder(GroqLLM(model=model_id).get_llm()).build_graph()
    for model_id in SUPPORTED_MODELS
}

# --- Thread store (replaces st.session_state.threads) ---
# thread_id -> [{"role": "user"/"assistant", "content": "..."}]
threads: dict[str, list] = {}


class ChatRequest(BaseModel):
    thread_id: str
    message: str
    model: str = SUPPORTED_MODELS[0]


# --- New Chat (replaces "+ New Chat" button) ---
@app.post("/api/threads")
def create_thread():
    tid = str(uuid.uuid4())[:8]
    threads[tid] = []
    return {"thread_id": tid}


# --- Thread list for sidebar (replaces sidebar thread buttons) ---
@app.get("/api/threads")
def get_threads():
    result = []
    for tid, msgs in threads.items():
        first_msg = next(
            (m["content"][:30] for m in msgs if m["role"] == "user"),
            f"Chat {tid}",
        )
        result.append({"id": tid, "first_message": first_msg})
    return list(reversed(result))


# --- Chat + streaming (replaces st.write_stream + token_stream) ---
@app.post("/api/chat")
async def chat(req: ChatRequest):
    thread_id = req.thread_id
    message = req.message

    if thread_id not in threads:
        threads[thread_id] = []
    threads[thread_id].append({"role": "user", "content": message})

    graph = graphs.get(req.model, graphs[SUPPORTED_MODELS[0]])

    async def event_stream():
        config = {"configurable": {"thread_id": thread_id}}
        full = ""
        tools_used: list[str] = []
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        # Run graph.stream in a thread (same call as app.py token_stream)
        def sync_stream():
            try:
                for chunk, metadata in graph.stream(
                    {"messages": [HumanMessage(content=message)]},
                    config=config,
                    stream_mode="messages",
                ):
                    loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, ("error", e))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

        threading.Thread(target=sync_stream, daemon=True).start()

        try:
            while True:
                kind, payload = await queue.get()

                if kind == "error":
                    err = str(payload)
                    if "INVALID_CHAT_HISTORY" in err or "tool_calls" in err:
                        new_tid = str(uuid.uuid4())[:8]
                        threads[new_tid] = []
                        msg = "⚠️ Session history was corrupted. A new chat has been started — please resend your message."
                        yield f"data: {json.dumps({'type': 'error', 'content': msg, 'new_thread_id': new_tid})}\n\n"
                    else:
                        msg = f"⚠️ {err}"
                        yield f"data: {json.dumps({'type': 'error', 'content': msg})}\n\n"
                    full = msg
                    break

                if kind == "done":
                    break

                chunk = payload

                # ToolMessage → emit tool status (replaces status.caption)
                if isinstance(chunk, ToolMessage):
                    tool_name = getattr(chunk, "name", "tool")
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)
                    yield f"data: {json.dumps({'type': 'tool', 'tools': tools_used})}\n\n"
                    continue

                has_tool_calls = bool(getattr(chunk, "tool_calls", [])) or \
                                 bool(getattr(chunk, "tool_call_chunks", []))
                if has_tool_calls:
                    continue

                # AI token → emit content (replaces yield chunk.content)
                if isinstance(chunk, (AIMessageChunk, AIMessage)) and chunk.content:
                    full += chunk.content
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

        finally:
            if full:
                threads[thread_id].append({"role": "assistant", "content": full})
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000,reload=True)