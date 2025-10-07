from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from . import models


def get_agent_by_token(db: Session, token: str) -> Optional[models.Agent]:
    stmt = select(models.Agent).where(models.Agent.token == token)
    return db.execute(stmt).scalars().first()


def get_agent_by_id(db: Session, agent_id: str) -> Optional[models.Agent]:
    return db.get(models.Agent, agent_id)


def upsert_agent(db: Session, *, agent_id: str, hostname: str, os: str, version: str, token: str) -> models.Agent:
    agent = get_agent_by_id(db, agent_id)
    if agent:
        agent.hostname = hostname
        agent.os = os
        agent.version = version
        agent.token = token
    else:
        agent = models.Agent(id=agent_id, hostname=hostname, os=os, version=version, token=token)
        db.add(agent)
    agent.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return agent


def update_last_seen(db: Session, agent: models.Agent) -> models.Agent:
    agent.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return agent


def create_task(db: Session, *, target_agent_id: str, type_: str, payload: dict) -> models.Task:
    task = models.Task(target_agent_id=target_agent_id, type=type_, payload_json=payload, status="queued")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_pending_tasks(db: Session, *, agent_id: str, limit: int = 10) -> List[models.Task]:
    stmt = (
        select(models.Task)
        .where(models.Task.target_agent_id == agent_id, models.Task.status == "queued")
        .order_by(models.Task.id.asc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def mark_task_running(db: Session, task: models.Task) -> models.Task:
    task.status = "running"
    db.commit()
    db.refresh(task)
    return task


def save_result(db: Session, *, task: models.Task, agent_id: str, status: str, output: dict) -> models.Result:
    result = models.Result(task_id=task.id, agent_id=agent_id, status=status, output_json=output)
    db.add(result)
    task.status = "done" if status == "ok" else "error"
    db.commit()
    db.refresh(result)
    return result


def list_agents(db: Session) -> List[models.Agent]:
    stmt = select(models.Agent).order_by(models.Agent.last_seen.desc())
    return list(db.execute(stmt).scalars().all())


def list_tasks(db: Session, *, agent_id: Optional[str] = None, status: Optional[str] = None) -> List[models.Task]:
    stmt = select(models.Task)
    if agent_id:
        stmt = stmt.where(models.Task.target_agent_id == agent_id)
    if status:
        stmt = stmt.where(models.Task.status == status)
    stmt = stmt.order_by(models.Task.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def audit(db: Session, *, actor: str, action: str, resource: str) -> models.Audit:
    entry = models.Audit(actor=actor, action=action, resource=resource)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
