from __future__ import annotations

import asyncio
import html
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

from orchestrator.agents import CritiqueAgent, RetrievalAgent, SynthesisAgent
from orchestrator.config import settings
from orchestrator.memory.store import PersistentMemoryStore
from orchestrator.messaging import AutoGenMessageBus
from orchestrator.models import Job, ResearchRequest
from orchestrator.queue import AsyncJobQueue
from orchestrator.tools.code_executor import CodeExecutionTool
from orchestrator.tools.registry import ToolRegistry
from orchestrator.tools.vector_retrieval import VectorRetrievalTool
from orchestrator.tools.web_search import WebSearchTool
from orchestrator.workflow import MultiAgentWorkflow


DEMO_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Multi-Agent LLM Orchestration Platform Demo</title>
    <style>
        :root {
            --bg: #0b1a24;
            --panel: #102838;
            --panel-soft: #15364b;
            --ink: #eaf2f8;
            --ink-soft: #a9bfce;
            --accent: #ff9f1c;
            --ok: #2ec4b6;
            --warn: #ffbf69;
            --err: #e76f51;
            --border: #24506a;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: "Segoe UI", "Trebuchet MS", sans-serif;
            color: var(--ink);
            background: radial-gradient(circle at 20% 0%, #14344a 0%, var(--bg) 45%);
            min-height: 100vh;
        }
        .wrap { max-width: 1040px; margin: 28px auto; padding: 0 16px; }
        h1 { margin: 0 0 6px; font-size: 2rem; letter-spacing: 0.3px; }
        p { margin: 0; color: var(--ink-soft); }
        .grid { display: grid; gap: 16px; margin-top: 20px; grid-template-columns: 1.2fr 1fr; }
        .card {
            background: linear-gradient(180deg, var(--panel) 0%, var(--panel-soft) 100%);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        label { display: block; margin: 10px 0 6px; font-weight: 600; }
        input, textarea, button {
            width: 100%;
            border-radius: 10px;
            border: 1px solid var(--border);
            color: var(--ink);
            background: #0f2533;
            padding: 10px 12px;
            font-size: 0.95rem;
        }
        textarea { min-height: 86px; resize: vertical; }
        button {
            background: linear-gradient(90deg, #f48c06, var(--accent));
            color: #1a1300;
            border: none;
            font-weight: 700;
            cursor: pointer;
            margin-top: 12px;
        }
        button:hover { filter: brightness(1.05); }
        .status {
            font-weight: 700;
            border-radius: 999px;
            display: inline-block;
            padding: 4px 10px;
            margin-top: 8px;
            background: #1e3c50;
        }
        .status.ok { background: rgba(46, 196, 182, 0.2); color: var(--ok); }
        .status.run { background: rgba(255, 191, 105, 0.2); color: var(--warn); }
        .status.err { background: rgba(231, 111, 81, 0.2); color: var(--err); }
        .samples { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        .sample-chip {
            width: auto;
            border: 1px solid #2f6a86;
            background: #153447;
            color: #bee4fa;
            padding: 8px 10px;
            border-radius: 999px;
            font-size: 0.84rem;
        }
        .mono {
            font-family: Consolas, "Courier New", monospace;
            white-space: pre-wrap;
            font-size: 0.88rem;
            background: #0d202d;
            border: 1px solid #23485e;
            border-radius: 10px;
            padding: 12px;
            max-height: 440px;
            overflow: auto;
        }
        .row { display: flex; gap: 10px; }
        .row > div { flex: 1; }
        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="wrap">
        <h1>Multi-Agent LLM Orchestration Platform</h1>
        <p>Live demo UI with sample data for retrieval, synthesis, and critique workflow.</p>

        <div class="grid">
            <section class="card">
                <h2 style="margin-top:0;">Run Sample Job</h2>
                <form id="runForm" method="post" action="/demo/run">
                <div class="row">
                    <div>
                        <label for="session">Session ID</label>
                        <input id="session" name="session_id" value="demo-session-1" />
                    </div>
                    <div>
                        <label for="topic">Topic</label>
                        <input id="topic" name="topic" value="How multi-agent systems reduce research latency?" />
                    </div>
                </div>

                <label for="constraints">Constraints (one per line)</label>
                <textarea id="constraints" name="constraints">Focus on measurable outcomes\nInclude deployment practicality</textarea>

                <div class="samples" id="samples"></div>
                <button id="runBtn" type="submit">Submit Job</button>
                <div id="jobStatus" class="status">idle</div>
                </form>
            </section>

            <section class="card">
                <h2 style="margin-top:0;">Service Health</h2>
                <div id="health" class="mono">Checking /health ...</div>
            </section>
        </div>

        <section class="card" style="margin-top:16px;">
            <h2 style="margin-top:0;">Latest Job Output</h2>
            <div id="output" class="mono">No job run yet.</div>
        </section>
    </div>

    <script>
        const samplePayloads = [
            {
                session_id: "sample-1",
                topic: "How multi-agent systems reduce research latency?",
                constraints: ["Focus on measurable outcomes", "Mention concurrent session safety"],
            },
            {
                session_id: "sample-2",
                topic: "Best strategy to productionize agent workflows in startups",
                constraints: ["Keep under 250 words", "Include trade-offs"],
            },
            {
                session_id: "sample-3",
                topic: "How to benchmark orchestration throughput objectively",
                constraints: ["Use repeatable metrics", "Highlight failure modes"],
            },
        ];

        const healthEl = document.getElementById("health");
        const outputEl = document.getElementById("output");
        const statusEl = document.getElementById("jobStatus");
        const runBtn = document.getElementById("runBtn");
        const runForm = document.getElementById("runForm");
        const samplesEl = document.getElementById("samples");
        const sessionEl = document.getElementById("session");
        const topicEl = document.getElementById("topic");
        const constraintsEl = document.getElementById("constraints");

        function setStatus(text, kind) {
            statusEl.textContent = text;
            statusEl.className = "status";
            if (kind) {
                statusEl.classList.add(kind);
            }
        }

        function constraintsFromText(text) {
            return text
                .split("\n")
                .map((line) => line.trim())
                .filter((line) => line.length > 0);
        }

        async function apiFetch(url, options = {}, timeoutMs = 10000) {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), timeoutMs);
            try {
                return await fetch(url, { ...options, signal: controller.signal });
            } finally {
                clearTimeout(timer);
            }
        }

        async function loadHealth() {
            try {
                const response = await apiFetch("/health", {}, 5000);
                const data = await response.json();
                healthEl.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                healthEl.textContent = "Health check failed: " + String(error);
            }
        }

        async function pollJob(jobId) {
            const maxAttempts = 40;
            for (let i = 0; i < maxAttempts; i += 1) {
                const response = await apiFetch(`/jobs/${jobId}`, {}, 7000);
                if (!response.ok) {
                    const err = await response.text();
                    outputEl.textContent = "Polling failed:\n" + err;
                    setStatus("error", "err");
                    return;
                }
                const data = await response.json();
                outputEl.textContent = JSON.stringify(data, null, 2);

                if (data.status === "completed") {
                    setStatus("completed", "ok");
                    return;
                }
                if (data.status === "failed") {
                    setStatus("failed", "err");
                    return;
                }

                setStatus("running", "run");
                await new Promise((resolve) => setTimeout(resolve, 250));
            }
            setStatus("timeout", "err");
        }

        async function submitJob() {
            runBtn.disabled = true;
            try {
                if (window.location.protocol !== "http:" && window.location.protocol !== "https:") {
                    outputEl.textContent = "Open the UI from the API server (http://127.0.0.1:8000/demo), not as a local file.";
                    setStatus("error", "err");
                    return;
                }

                const payload = {
                    session_id: sessionEl.value.trim(),
                    topic: topicEl.value.trim(),
                    constraints: constraintsFromText(constraintsEl.value),
                };

                if (payload.session_id.length < 3 || payload.topic.length < 3) {
                    outputEl.textContent = "Session ID and Topic must be at least 3 characters.";
                    setStatus("invalid input", "err");
                    return;
                }

                outputEl.textContent = "Submitting job...";
                setStatus("queued", "run");

                const response = await apiFetch("/jobs", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                }, 10000);

                if (!response.ok) {
                    const err = await response.text();
                    outputEl.textContent = "Job submission failed:\n" + err;
                    setStatus("error", "err");
                    return;
                }

                const job = await response.json();
                outputEl.textContent = JSON.stringify(job, null, 2);
                await pollJob(job.id);
            } catch (error) {
                outputEl.textContent = "Unexpected error: " + String(error);
                setStatus("error", "err");
            } finally {
                runBtn.disabled = false;
            }
        }

        samplePayloads.forEach((sample, index) => {
            const chip = document.createElement("button");
            chip.className = "sample-chip";
            chip.type = "button";
            chip.textContent = `Load sample ${index + 1}`;
            chip.addEventListener("click", () => {
                sessionEl.value = sample.session_id;
                topicEl.value = sample.topic;
                constraintsEl.value = sample.constraints.join("\n");
            });
            samplesEl.appendChild(chip);
        });

        runForm.addEventListener("submit", (event) => {
            event.preventDefault();
            submitJob();
        });
        loadHealth();
    </script>
</body>
</html>
"""


def build_app() -> FastAPI:
    memory = PersistentMemoryStore(settings.memory_db_path)
    tools = ToolRegistry()
    tools.register(WebSearchTool(fake_results=settings.enable_fake_tool_results))
    tools.register(VectorRetrievalTool(fake_results=settings.enable_fake_tool_results))
    tools.register(CodeExecutionTool())

    bus = AutoGenMessageBus()
    retrieval = RetrievalAgent(name="retrieval", memory=memory, tools=tools)
    synthesis = SynthesisAgent(name="synthesis", memory=memory, tools=tools)
    critique = CritiqueAgent(name="critique", memory=memory, tools=tools)

    workflow = MultiAgentWorkflow(
        retrieval_agent=retrieval,
        synthesis_agent=synthesis,
        critique_agent=critique,
        message_bus=bus,
    )

    queue = AsyncJobQueue(workflow=workflow, max_concurrent_jobs=settings.max_concurrent_jobs)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await queue.start()
        try:
            yield
        finally:
            await queue.stop()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"service": settings.app_name, "status": "running", "docs": "/docs"}

    @app.get("/demo", response_class=HTMLResponse)
    async def demo_ui() -> str:
        return DEMO_HTML

    @app.post("/demo/run", response_class=HTMLResponse)
    async def demo_run_form(
        session_id: str = Form(...),
        topic: str = Form(...),
        constraints: str = Form(""),
    ) -> str:
        request = ResearchRequest(
            session_id=session_id.strip(),
            topic=topic.strip(),
            constraints=[line.strip() for line in constraints.splitlines() if line.strip()],
        )
        result = await asyncio.to_thread(workflow.run, request)
        rendered = html.escape(json.dumps(result.model_dump(), indent=2))
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>Demo Result</title>"
            "<style>body{font-family:Segoe UI,Trebuchet MS,sans-serif;padding:20px;background:#0b1a24;color:#eaf2f8;}"
            "a{color:#ffbf69;}pre{background:#0d202d;border:1px solid #23485e;padding:12px;border-radius:8px;"
            "white-space:pre-wrap;}</style></head><body>"
            "<h2>Sample Job Result</h2><p><a href='/demo'>Back to Demo UI</a></p>"
            f"<pre>{rendered}</pre></body></html>"
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/jobs", response_model=Job)
    async def submit_job(request: ResearchRequest) -> Job:
        return await queue.submit(request)

    @app.get("/jobs/{job_id}", response_model=Job)
    async def get_job(job_id: str) -> Job:
        job = await queue.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    return app


app = build_app()
