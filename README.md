# AI Chatbot

A conversational AI chatbot built with **Streamlit**, **LangGraph**, and **Groq** (LLaMA 3.3 70B). Supports multiple concurrent chat sessions with full conversation memory per thread.

## Features

- Multi-session chat — create and switch between independent conversations from the sidebar
- Streaming responses — tokens stream in real time as the model generates them
- Persistent memory per thread — each chat thread retains its full history using LangGraph's `MemorySaver`
- Professional system prompt — the assistant is instructed to be clear, concise, and honest
- LangSmith tracing support — optional observability via `LANGSMITH_API_KEY`

## Tech Stack

| Layer | Library |
|---|---|
| UI | Streamlit |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Orchestration | LangGraph (`StateGraph`) |
| LLM Abstraction | LangChain Core / LangChain Groq |
| Memory | LangGraph `MemorySaver` (in-memory) |
| Config | python-dotenv |

## Project Structure

```
Chatbot/
├── app.py                  # Streamlit UI entry point
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
└── src/
    ├── graphs/
    │   └── graph_builder.py    # Builds the LangGraph StateGraph
    ├── llms/
    │   └── groqllm.py          # Groq LLM initialization
    ├── nodes/
    │   └── blog_node.py        # ChatNode with system prompt logic
    └── states/
        └── blog_state.py       # ChatState TypedDict definition
```

## Architecture

```
User Input
    │
    ▼
Streamlit UI (app.py)
    │  sends HumanMessage
    ▼
LangGraph StateGraph
    │
    ├── START
    │     │
    │     ▼
    │  [chatbot node]  ←── SystemMessage + conversation history
    │     │  invokes Groq LLaMA 3.3 70B
    │     ▼
    └── END
         │
         ▼
  Streamed tokens → Streamlit chat UI
```

Each conversation thread gets its own `thread_id` used as the LangGraph config key, so memory is fully isolated between sessions.

## Setup

### Prerequisites

- Python 3.11+
- A [Groq](https://console.groq.com/) API key
- (Optional) A [LangSmith](https://smith.langchain.com/) API key for tracing

### Installation

```bash
# Clone the repo or navigate to the project directory
cd Chatbot

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here   # optional
```

### Run

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` by default.

## Usage

1. Type a message in the chat input at the bottom and press Enter.
2. The assistant responds with streamed output in real time.
3. Click **+ New Chat** in the sidebar to start a fresh conversation.
4. Previous chats are listed in the sidebar — click any to switch back to it.

## Dependencies

```
langchain
langgraph
langchain_community
langchain_core
langchain_groq
langchain-cli[inmem]
streamlit
python-dotenv
```

## Notes

- Conversation memory is in-process only. Restarting the Streamlit app clears all chat history.
- To persist history across restarts, replace `MemorySaver` in [graph_builder.py](src/graphs/graph_builder.py) with a database-backed checkpointer (e.g., `langgraph-checkpoint-sqlite`).
