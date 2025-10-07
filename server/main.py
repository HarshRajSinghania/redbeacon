from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import secrets
from typing import List

from .db import init_db, get_db
from . import schemas, models
from .config import settings
from .auth import require_admin, require_agent
from . import crud

app = FastAPI(title="RedBeacon C2", version="0.1.0")

# Very open CORS for demo use; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
def on_startup():
    init_db()


# -------- Agent endpoints --------
@app.post("/enroll", response_model=schemas.EnrollResponse)
def enroll(req: schemas.EnrollRequest, db: Session = Depends(get_db)):
    # Generate token only once per agent (or rotate if re-enrolling)
    token = secrets.token_hex(16)
    agent = crud.upsert_agent(
        db,
        agent_id=req.agent_id,
        hostname=req.hostname,
        os=req.os or "",
        version=req.version or "",
        token=token,
    )
    crud.audit(db, actor=agent.id, action="enroll", resource=agent.id)
    return schemas.EnrollResponse(agent_id=agent.id, token=agent.token)


@app.post("/heartbeat", response_model=schemas.HeartbeatResponse)
def heartbeat(agent=Depends(require_agent), db: Session = Depends(get_db)):
    crud.update_last_seen(db, agent)
    tasks = crud.list_pending_tasks(db, agent_id=agent.id, limit=10)
    response_tasks: List[schemas.TaskItem] = []
    for t in tasks:
        crud.mark_task_running(db, t)
        response_tasks.append(schemas.TaskItem(id=t.id, type=t.type, payload=t.payload_json))
    return schemas.HeartbeatResponse(tasks=response_tasks)


@app.post("/results")
def submit_results(req: schemas.ResultSubmit, agent=Depends(require_agent), db: Session = Depends(get_db)):
    task = db.get(models.Task, req.task_id)
    if not task or task.target_agent_id != agent.id:
        raise HTTPException(status_code=404, detail="Task not found for this agent")
    res = crud.save_result(db, task=task, agent_id=agent.id, status=req.status, output=req.output)
    crud.audit(db, actor=agent.id, action="submit_result", resource=f"task:{task.id}")
    return {"result_id": res.id}


# -------- Admin endpoints --------
@app.post("/tasks", dependencies=[Depends(require_admin)])
def create_task(req: schemas.CreateTaskRequest, db: Session = Depends(get_db)):
    agent = crud.get_agent_by_id(db, req.target_agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    task = crud.create_task(db, target_agent_id=req.target_agent_id, type_=req.type, payload=req.payload)
    crud.audit(db, actor="admin", action="create_task", resource=f"agent:{req.target_agent_id}")
    return {"task_id": task.id}


@app.get("/agents", response_model=List[schemas.AgentOut], dependencies=[Depends(require_admin)])
def get_agents(db: Session = Depends(get_db)):
    agents = crud.list_agents(db)
    return [
        schemas.AgentOut(
            id=a.id, hostname=a.hostname, os=a.os, version=a.version, last_seen=a.last_seen
        )
        for a in agents
    ]


@app.get("/tasks", response_model=List[schemas.TaskOut], dependencies=[Depends(require_admin)])
def get_tasks(agent_id: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    tasks = crud.list_tasks(db, agent_id=agent_id, status=status)
    return [
        schemas.TaskOut(
            id=t.id, target_agent_id=t.target_agent_id, type=t.type, status=t.status, created_at=t.created_at
        )
        for t in tasks
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.main:app", host=settings.host, port=settings.port, reload=False)
