# Multi-Agent LLM Orchestration Platform

A production-style reference implementation of a multi-agent research orchestration system using LangGraph state-machine flow, CrewAI-inspired role specialization, AutoGen-style inter-agent messaging, persistent memory, and a FastAPI async orchestration API.

## Why this project

Manual research workflows are slow and brittle when information must be gathered, cross-referenced, and synthesized across sources. This project demonstrates a self-contained orchestration layer that can automate retrieval, synthesis, and critique with concurrent session safety and measurable handoff latency.

## Highlights

- 4-agent style pipeline design (orchestrator + retrieval + synthesis + critique)
- LangGraph-first workflow integration with fallback execution path
- CrewAI-style role separation for specialist agents
- AutoGen-style message handoff bus with latency tracking
- Persistent memory via SQLite with session and agent partitioning
- Tool-calling interfaces: web search, vector retrieval, code execution
- FastAPI REST service with async job queue and concurrent workers
- Dockerized deployment for reproducible environments

## Architecture

1. Client submits a research request to FastAPI.
2. Request is queued in async workers.
3. Orchestrator runs retrieval -> synthesis -> critique as a state-machine.
4. Agent handoffs are tracked through message bus latency metrics.
5. Artifacts and summaries are returned through the job endpoint.
6. Agent memory is persisted in SQLite for cross-run context.

## Project structure

- src/orchestrator/api/main.py: API and DI wiring
- src/orchestrator/workflow.py: orchestration graph and fallback flow
- src/orchestrator/queue.py: async worker queue
- src/orchestrator/agents/: specialized agents
- src/orchestrator/tools/: pluggable tools
- src/orchestrator/memory/store.py: persistent agent memory
- tests/: API and workflow tests

## Quickstart

### 1) Create environment and install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

### 2) Run locally

```powershell
uvicorn orchestrator.api.main:app --host 0.0.0.0 --port 8000 --app-dir src
```

### 3) Call API

```powershell
curl -X POST http://localhost:8000/jobs -H "Content-Type: application/json" -d '{"session_id":"demo-1","topic":"How multi-agent systems reduce research latency?","constraints":["focus on measurable outcomes"]}'
```

Then poll:

```powershell
curl http://localhost:8000/jobs/<job_id>
```

## Docker

```powershell
docker compose up --build
```

## Make it live

### Option A: Render (recommended)

1. Push this repo to GitHub.
2. In Render, click New + -> Blueprint.
3. Select this repository (uses `render.yaml` automatically).
4. Deploy.

Your live URLs will be:

- `https://<your-render-service>.onrender.com/`
- `https://<your-render-service>.onrender.com/health`
- `https://<your-render-service>.onrender.com/docs`

### Option B: Railway

1. New Project -> Deploy from GitHub repo.
2. Railway detects `Dockerfile` automatically.
3. Set `PORT` if prompted (Railway usually injects it).
4. Deploy and open generated public URL.

## Benchmark notes

Local validation snapshot (single-machine smoke run):

- API health checks: passed (`/` and `/health`)
- Test suite: 3 passed
- End-to-end demo job status: completed
- End-to-end demo job total latency: 51 ms
- Handoff latencies reported: [0, 0]
- State collision incidents observed: 0

## GitHub publishing

```powershell
git init
git add .
git commit -m "feat: initial multi-agent llm orchestration platform"
git branch -M main
git remote add origin https://github.com/<your-username>/multi-agent-llm-orchestration-platform.git
git push -u origin main
```

## Resume alignment

This implementation is structured to support resume bullets around:

- LangGraph orchestration
- CrewAI-style delegation by agent role
- AutoGen-style inter-agent handoffs and latency tracking
- Persistent memory and tool-calling interfaces
- FastAPI async job orchestration and Dockerized deployment
