# System Overview

This document provides a comprehensive overview of the RAG-Scrape system architecture, configuration, and design decisions.

---

## 1. System Goals

The primary goal of RAG-Scrape is to systematically extract localized, hidden, and region-specific knowledge from community forums.
Forums (like Voz) contain valuable discussions, but they are buried under pages of noise, spam, and signatures.
This system solves this by scraping threads, extracting valuable text content, indexing it into a local Vector DB, and synthesizing answers via a Gemini LLM.

---

## ## 2. Directory Layout

The codebase strictly adheres to the following layout:

```text
├── .github/
│   └── workflows/
│       └── ci.yml      # CI workflow for pytest runs
├── docs/
│   ├── system_overview.md   # Architectural documentation (this file)
│   ├── handoff_notes.md     # Session handoff notes for the next agent
│   └── LESSONS_LEARNED.md   # Persistent learnings database
├── src/
│   ├── graph/
│   │   ├── nodes/
│   │   │   ├── rag_node.py       # Retrieves indexed history from Vector DB
│   │   │   └── scraper_node.py   # Scrapes URL, chunks, and indexes thread
│   │   ├── graph.py              # Compiles nodes and edges into LangGraph
│   │   ├── router.py             # Router logic using ChatGoogleGenerativeAI
│   │   ├── schemas.py            # Pydantic schemas for structured LLM outputs
│   │   └── state.py              # LangGraph TypedDict State declaration
│   ├── rag/
│   │   ├── chunker.py       # Segment text using character text splitter
│   │   ├── core.py          # ChromaDB persistent/server client connection
│   │   └── embeddings.py    # Instantiates Gemini embeddings client
│   ├── scraper/
│   │   ├── core.py          # Polite HTTP fetch, robots.txt, rate limit, saved-page loader
│   │   ├── exceptions.py    # Raised when a site refuses automated access
│   │   └── voz_parser.py    # BeautifulSoup XenForo selector parser
│   ├── config.py            # Pydantic settings management
│   ├── log_config.py        # Structured JSON formatter and logging setup
│   └── observability.py     # Lazy-loaded Langfuse tracing callback
├── tests/                   # Extensive unit and E2E offline test suite
├── Dockerfile               # Multi-stage, uv-based runtime container
├── docker-compose.yml       # Standalone ChromaDB server and CLI orchestrator
├── main.py                  # Entrypoint for the CLI application
└── pyproject.toml           # Project dependency definitions
```

---

## 3. Core Component Design

### LangGraph Control Flow
The execution flow is modeled as a Directed Acyclic Graph (DAG) using LangGraph.
It manages state updates in an isolated `AgentState` TypedDict.
Nodes return dictionary updates that the graph applies to the State.
A conditional router bypasses the LLM classification entirely if a direct URL is supplied.
This reduces Gemini API costs and execution latency.

### Polite Fetching
Threads are fetched with plain HTTP, an honest User-Agent, a `robots.txt` check, and a 2-second per-host rate limit.
Anti-bot challenges are never solved or bypassed: the fetch stops with `ForumBlockedException`.
In that case the user saves the thread page from a browser and indexes it with `main.py ingest <file>`.
There is no keyword search command; discovering threads is left to the user's browser.

### Dynamic Storage Swapping
We support two modes of ChromaDB operation:
1. **PersistentClient (In-Process):** Saves data to a local folder (`./chroma_data`).
   This is ideal for local development and offline unit testing.
2. **HttpClient (Client-Server):** Connects to a standalone ChromaDB server container in Docker Compose.
   This is configured via `CHROMA_SERVER_HOST` and `CHROMA_SERVER_PORT`.

### Observability & Structured Logging
We format logs as single-line JSON records using a custom `JsonFormatter` when `LOG_FORMAT=json` is set.
We lazy-load the Langfuse `CallbackHandler` using credentials in settings.
It is injected into the graph's `config` parameters on execution, tracing all LLM invocations and node transitions.
