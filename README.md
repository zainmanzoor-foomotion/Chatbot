# AI Chatbot

A conversational AI chatbot built with **React + Vite**, **FastAPI**, **LangGraph**, and **Groq API**. Supports multiple concurrent chat sessions with full conversation memory per thread and real-time streaming responses.

## Features

- Multi-session chat — create and switch between independent conversations from the sidebar
- Streaming responses — tokens stream in real time via Server-Sent Events (SSE)
- Persistent memory per thread — each chat thread retains its full history using LangGraph's `MemorySaver`
- Regenerate — re-run any assistant response with one click
- Copy — copy any assistant message to clipboard
- LangSmith tracing support — optional observability via `LANGSMITH_API_KEY`
- **Integrated Tools** — AI assistant has access to multiple tools:
  - **ArXiv Search** — Search academic papers and research
  - **Wikipedia Lookup** — Access encyclopedic information
  - **Real-time Weather** — Current weather data for any city worldwide
  - **Crypto Prices** — Real-time cryptocurrency prices and market data via CoinGecko
  - **Web Search** — Powered by Tavily for current news and web content

## Tech Stack

| Layer | Library / Tool |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI, Uvicorn |
| LLM | Groq (Multiple Models Available) |
| Available Models | GPT OSS 20B (`openai/gpt-oss-20b`)<br/>Qwen3 32B (`qwen/qwen3-32b`)<br/>LLama 3.3 70B (`llama-3.3-70b-versatile`) |
| Orchestration | LangGraph (`StateGraph`) |
| LLM Abstraction | LangChain Core / LangChain Groq |
| Memory | LangGraph `MemorySaver` (in-memory) |
| Tool Input Validation | Pydantic `args_schema` |
| Tools | LangChain Community (ArXiv, Wikipedia), Custom (Weather, Crypto), Tavily Search |
| Streaming | Server-Sent Events (SSE) via `StreamingResponse` |
| Config | python-dotenv |
## Project Structure

```
Chatbot/
├── server/                         # Python backend (FastAPI + LangGraph)
│   ├── app.py                      # FastAPI entry point + SSE streaming
│   ├── requirements.txt            # Python dependencies
│   ├── pyproject.toml              # Project metadata
│   ├── .env                        # Environment variables
│   └── src/
│       ├── graphs/
│       │   └── graph_builder.py    # Builds the LangGraph StateGraph
│       ├── llms/
│       │   └── groqllm.py          # Groq LLM initialization
│       ├── nodes/
│       │   └── node.py             # ChatNode — system prompt + tool binding
│       ├── states/
│       │   └── state.py            # ChatState TypedDict definition
│       └── tools/
│           └── tools.py            # Tools with Pydantic input/output schemas
│
└── client/                         # React frontend (Vite + Tailwind)
    ├── index.html
    ├── vite.config.ts              # Vite config with /api proxy
    ├── tailwind.config.js
    └── src/
        ├── main.tsx
        ├── App.tsx                 # Global state, streaming logic
        ├── types.ts
        └── components/
            ├── Sidebar.tsx         # Thread list + New Chat
            ├── ChatArea.tsx        # Message list + thinking indicator
            ├── MessageBubble.tsx   # User/assistant message + copy + regenerate
            └── ChatInput.tsx       # Textarea input + send button
```

## Architecture

```
User Input (React)
    │
    ▼  POST /api/chat  (JSON)
FastAPI  app.py
    │  runs graph.stream() in a background thread
    │  emits SSE events: token | tool | error | done
    ▼
LangGraph StateGraph
    │
    ├── START
    │     ▼
    │  [ModelTool node]  ←── SystemPrompt + conversation history
    │     │  Groq Qwen3 32B with tools bound
    │     ▼
    │  tools_condition()
    │     │                    │
    │     ▼                    ▼
    │  [tooSupportsls node]           END
    │     │  ArXiv / Wikipedia /
    │     │  Weather / Crypto /
    │     │  Tavily Search
    │     ▼
    │  [ModelTool node]  (loop — processes tool results)
    │     ▼
    └── END
         │
         ▼  SSE token stream
React ChatArea (renders markdown in real time)
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Groq](https://console.groq.com/) API key
- (Optional) A [LangSmith](https://smith.langchain.com/) API key for tracing
- (Optional) An [OpenWeather](https://openweathermap.org/api) API key for weather
- (Optional) A [Tavily](https://tavily.com/) API key for web search

### 1 — Backend

```bash
cd Chatbot/server

# Install dependencies
pip install -r requirements.txt
```

Create `server/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here     # optional
OPENWEATHER_API_KEY=your_openweather_api_key_here # optional
TAVILY_API_KEY=your_tavily_api_key_here           # optional
```

Start the server:

```bash
python -m uvicorn app:app --reload --port 8000
```

### 2 — Frontend

```bash
cd Chatbot/client

npm install
npm run dev
```

Open `http://localhost:5173`.

## Usage

1. Type a message and press **Enter** (or click the send button).
2. The assistant responds with streamed output in real time.
3. Click **+ New Chat** in the sidebar to start a fresh conversation.
4. Previous chats are listed in the sidebar — click any to switch.
5. Click **↻ Regenerate** below any assistant message to get a new response.
6. Click **Copy** to copy any assistant message to clipboard.

### Tool Usage Examples

| Query | Tool Used |
|---|---|
| "Search for papers about transformer models" | ArXiv |
| "Tell me about the Roman Empire" | Wikipedia |
| "What's the weather in Tokyo?" | OpenWeather |
| "Price of Bitcoin / Pi coin / Ethereum" | CoinGecko |
| "Latest AI news this week" | Tavily Search |

## Notes

- Conversation memory is in-process only — restarting the server clears all chat history.
- To persist history, replace `MemorySaver` in [server/src/graphs/graph_builder.py](server/src/graphs/graph_builder.py) with a database-backed checkpointer with a database-backed checkpointer (e.g. `langgraph-checkpoint-sqlite`).
- Crypto prices use CoinGecko's free API — no key required. Ambiguous coin names (e.g. "pi coin") are resolved automatically via CoinGecko's search endpoint.
- The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`, so no CORS issues during development.
