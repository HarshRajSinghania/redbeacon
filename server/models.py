from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    hostname = Column(String, nullable=False)
    os = Column(String, nullable=True)
    version = Column(String, nullable=True)
    token = Column(String, nullable=False, index=True, unique=True)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    tasks = relationship("Task", back_populates="agent")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # e.g., inventory, metrics, logs
    payload_json = Column(JSON, nullable=False, default={})
    status = Column(String, nullable=False, default="queued")  # queued, running, done, error
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent", back_populates="tasks")
    result = relationship("Result", back_populates="task", uselist=False)


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="ok")  # ok, error
    output_json = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("Task", back_populates="result")


class Audit(Base):
    __tablename__ = "audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
