from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from orchestration.graph import research_graph
import uuid, asyncio

app = FastAPI(title="AgentOps", description="Multi-Agent Research Platform", version="1.0.0")

jobs = {}


class ResearchRequest(BaseModel):
    query: str


class ResearchResponse(BaseModel):
    job_id: str
    status: str
    report: str | None = None


@app.post("/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "report": None}
    background_tasks.add_task(execute_research, job_id, request.query)
    return ResearchResponse(job_id=job_id, status="running")


@app.get("/research/{job_id}", response_model=ResearchResponse)
async def get_result(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return ResearchResponse(job_id=job_id, status="not_found")
    return ResearchResponse(job_id=job_id, **job)


async def execute_research(job_id: str, query: str):
    try:
        result = await asyncio.to_thread(
            research_graph.invoke,
            {"query": query, "retrieved_docs": [], "analysis": "",
             "critique": "", "final_report": "", "iteration": 0}
        )
        jobs[job_id] = {"status": "completed", "report": result["final_report"]}
    except Exception as e:
        jobs[job_id] = {"status": "failed", "report": str(e)}


@app.get("/health")
def health():
    return {"status": "ok"}
