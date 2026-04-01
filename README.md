# AI Chatbot

A conversational AI chatbot built with **Streamlit**, **LangGraph**, and **Groq** (LLaMA 3.3 70B). Supports multiple concurrent chat sessions with full conversation memory per thread.

## Features

- Multi-session chat — create and switch between independent conversations from the sidebar
- Streaming responses — tokens stream in real time as the model generates them
- Persistent memory per thread — each chat thread retains its full history using LangGraph's `MemorySaver`
- Professional system prompt — the assistant is instructed to be clear, concise, and honest
- LangSmith tracing support — optional observability via `LANGSMITH_API_KEY`
- **Integrated Tools** — AI assistant has access to multiple tools for enhanced capabilities:
  - **ArXiv Search** — Search academic papers and research
  - **Wikipedia Lookup** — Access encyclopedic information and explanations
  - **Real-time Weather** — Get current weather data for any city worldwide
  - **Crypto Prices** — Real-time cryptocurrency prices and market data (Bitcoin, Ethereum, etc.)
  - **Web Search** — Powered by Tavily for current news and web content

## Tech Stack

| Layer | Library |
|---|---|
| UI | Streamlit |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Orchestration | LangGraph (`StateGraph`) |
| LLM Abstraction | LangChain Core / LangChain Groq |
| Memory | LangGraph `MemorySaver` (in-memory) |
| Tools | LangChain Community (ArXiv, Wikipedia), Custom (Weather, Crypto), Tavily Search |
| Config | python-dotenv |

## Project Structure

```
Chatbot/
├── app.py                  # Streamlit UI entry point
├── main.py                 # CLI entry point (placeholder)
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
└── src/
    ├── graphs/
    │   └── graph_builder.py    # Builds the LangGraph StateGraph
    ├── llms/
    │   └── groqllm.py          # Groq LLM initialization
    ├── nodes/
    │   └── blog_node.py        # ChatNode with system prompt and tool logic
    ├── states/
    │   └── blog_state.py       # ChatState TypedDict definition
    └── tools/
        └── tools.py            # Integrated tools (ArXiv, Wikipedia, Weather, Crypto, Tavily)
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
- (Optional) An [OpenWeather](https://openweathermap.org/api) API key for weather functionality
- (Optional) A [Tavily](https://tavily.com/) API key for enhanced web search

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
OPENWEATHER_API_KEY=your_openweather_api_key_here   # optional, for weather
TAVILY_API_KEY=your_tavily_api_key_here   # optional, for enhanced web search
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

### Tool Usage Examples

The AI assistant can help you with various tasks using its integrated tools:

- **Academic Research**: "Search for papers about machine learning transformers"
- **General Knowledge**: "Tell me about quantum computing"
- **Weather**: "What's the weather like in Tokyo right now?"
- **Cryptocurrency**: "What's the current price of Bitcoin?" or "Show me Ethereum market data"
- **Web Search**: "What are the latest developments in AI this week?"

The assistant automatically determines which tool to use based on your request.

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
arxiv
wikipedia
requests
langchain-tavily
tavily-python
```

## Notes

- Conversation memory is in-process only. Restarting the Streamlit app clears all chat history.
- To persist history across restarts, replace `MemorySaver` in [graph_builder.py](src/graphs/graph_builder.py) with a database-backed checkpointer (e.g., `langgraph-checkpoint-sqlite`).
- **Crypto prices** are fetched from CoinGecko API (free tier, no authentication required).
- **Weather data** requires an OpenWeather API key for full functionality.
- **Web search** works best with a Tavily API key for comprehensive results.
- Tools are automatically selected based on user queries - no manual tool selection needed.
