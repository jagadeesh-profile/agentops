# AgentOps — Autonomous Multi-Agent Research & Synthesis Platform

A production-grade multi-agent orchestration system that autonomously gathers, cross-references, and synthesizes research from multiple sources — no human in the loop required.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange?style=flat)
![CrewAI](https://img.shields.io/badge/CrewAI-0.28+-green?style=flat)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal?style=flat&logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-ready-blue?style=flat&logo=docker)

---

## What It Does

AgentOps coordinates four specialized AI agents to handle complex research tasks end-to-end:

| Agent | Role |
|-------|------|
| **Retriever** | Fetches relevant documents from web + vector store |
| **Analyst** | Extracts key facts and cross-references sources |
| **Critic** | Validates claims, flags contradictions |
| **Synthesizer** | Produces final structured report |

## Architecture

```
User Query
    │
    ▼
LangGraph State Machine
    │
    ├─► Retriever Agent  (ChromaDB + Web Search)
    │         │
    ├─► Analyst Agent    (GPT-4 / LLaMA 3)
    │         │
    ├─► Critic Agent     (Validation + Guardrails)
    │         │
    └─► Synthesizer Agent ──► Final Report
              │
              ▼
        FastAPI Response
```

## Screenshots

### Agent workflow running
![Agent Run](docs/screenshots/agent_run.png)

### FastAPI Swagger UI
![API Docs](docs/screenshots/api_docs.png)

### Sample synthesized output
![Output](docs/screenshots/output_sample.png)

## Results

| Metric | Value |
|--------|-------|
| Research workflow time reduction | ~70% vs manual |
| Agent handoff latency | < 3 seconds |
| Concurrent sessions (zero state collision) | ✓ |
| Agents in pipeline | 4 |

## Project Structure

```
agentops/
├── agents/
│   ├── retriever.py        # Document retrieval + web search
│   ├── analyst.py          # Fact extraction + cross-referencing
│   ├── critic.py           # Validation + guardrails
│   └── synthesizer.py      # Final report generation
├── orchestration/
│   ├── graph.py            # LangGraph state machine definition
│   └── memory.py           # Persistent agent memory (ChromaDB)
├── api/
│   └── main.py             # FastAPI endpoints + async job queue
├── tools/
│   ├── search.py           # Web search tool
│   └── vector_store.py     # ChromaDB wrapper
├── tests/
│   └── test_pipeline.py
├── docker/
│   └── Dockerfile
├── docs/
│   └── screenshots/
├── .env.example
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/jagadeeshpamidi/agentops.git
cd agentops

# 2. Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Add your API keys
cp .env.example .env
# Edit .env: OPENAI_API_KEY, TAVILY_API_KEY

# 4. Run the API
uvicorn api.main:app --reload

# 5. Send a research query
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Latest advances in RAG systems 2025"}'
```

## Tech Stack

- **Orchestration:** LangGraph, CrewAI, AutoGen
- **LLMs:** GPT-4, LLaMA 3 (via Ollama)
- **Vector Memory:** ChromaDB
- **Serving:** FastAPI + async job queue
- **Deployment:** Docker

---
Built by [Jagadeesh Pamidi](https://github.com/jagadeeshpamidi)
