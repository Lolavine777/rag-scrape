# Handoff Notes

This document provides a handoff summary for developers or agents continuing work on the RAG-Scrape project.

---

## 1. Project State

* **Active Branch:** `main` (Fully up to date with remote repository).
* **Git Status:** Clean (All features and documentation commits are completed).
* **Local Test Suite:** 40/40 tests passing successfully in `10.39s` (Runs completely offline).
* **GitHub Actions CI:** Fully operational (Fixed virtual environment dependency checks by using `uv sync`).

---

## 2. Component Reference

* **CLI Command Entrypoint ([main.py](file:///d:/projects/personal_projects/scraping-tool/main.py)):** Exposes `ask`, `search`, and `--reset-db` commands.
* **Vector DB Client ([core.py](file:///d:/projects/personal_projects/scraping-tool/src/rag/core.py)):** Instantiates either `PersistentClient` or `HttpClient` dynamically based on `settings.chroma_server_host`.
* **Google-Bypass Search Scraper ([voz_search.py](file:///d:/projects/personal_projects/scraping-tool/src/scraper/voz_search.py)):** Performs google queries with `StealthyFetcher` and cleans Google redirects.
* **Observability singleton ([observability.py](file:///d:/projects/personal_projects/scraping-tool/src/observability.py)):** Caches and exposes the Langfuse callback client handler.
* **Structured Logger ([log_config.py](file:///d:/projects/personal_projects/scraping-tool/src/log_config.py)):** Manages JSON log formatting and mutes noisy third-party loggers.

---

## 3. Future Roadmap Suggestions

If you are tasked to extend this repository, consider implementing the following features:

### Feature 1: Multi-Page Thread Scraping
Extend the scraping node to traverse multi-page XenForo threads.
Add `current_page` and `max_pages` fields to `AgentState` in [state.py](file:///d:/projects/personal_projects/scraping-tool/src/graph/state.py).
Update `scraper_node` to parse nextPage links from XenForo pagination HTML elements (`.pageNav-jump--next`).
Create a conditional edge loop in [graph.py](file:///d:/projects/personal_projects/scraping-tool/src/graph/graph.py) that loops back to `scraper_node` until all pages are retrieved.

### Feature 2: XenForo User Authentication Session Support
Add login capabilities to bypass potential login-restricted threads.
Create a config parameter `voz_username` and `voz_password` in [config.py](file:///d:/projects/personal_projects/scraping-tool/src/config.py).
Implement a login POST request in `src/scraper/core.py` to extract XenForo session cookies and pass them into the `StealthyFetcher` headers.

### Feature 3: LLM Rate-limiting (429) fallback
Implement a try-except fallback in `generator_node`.
If the Gemini API throws a quota exception, catch it, log a warning, and output the raw database chunks retrieved from ChromaDB instead of crashing.

---

## 4. Debugging & Maintenance Cheatsheet

### Vector Database Mocking
ChromaDB collections enforce the vector dimension (768 for Gemini).
When writing new test mocks, ensure mock embedding vectors generated are exactly 768 elements long.
Failure to do so will trigger a `chromadb.errors.InvalidArgumentError`.

### Windows Console Unicode Crashes
Printing raw Vietnamese diacritics directly to a Windows shell command terminal (CP1252/cmd) will raise a `UnicodeEncodeError`.
Always filter out non-ASCII characters or format console output cleanly using explicit utf-8 print parameters where applicable.

### Offline Testing
Ensure tests run without active network calls.
Always mock out `fetch_voz_thread` in scraper tests and `GoogleGenerativeAIEmbeddings` in RAG tests.
This keeps execution speed under 11 seconds and makes builds highly reliable.
