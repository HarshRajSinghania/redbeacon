from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Agent models
class EnrollRequest(BaseModel):
    agent_id: str = Field(..., description="Stable unique ID for the agent (e.g., UUID)")
    hostname: str
    os: Optional[str] = None
    version: Optional[str] = None


class EnrollResponse(BaseModel):
    agent_id: str
    token: str


class HeartbeatRequest(BaseModel):
    # Reserved for future fields
    pass


class TaskItem(BaseModel):
    id: int
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class HeartbeatResponse(BaseModel):
    tasks: List[TaskItem] = Field(default_factory=list)


class ResultSubmit(BaseModel):
    task_id: int
    status: str = Field(pattern="^(ok|error)$")
    output: Dict[str, Any] = Field(default_factory=dict)


# Admin API
class CreateTaskRequest(BaseModel):
    target_agent_id: str
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class AgentOut(BaseModel):
    id: str
    hostname: str
    os: Optional[str]
    version: Optional[str]
    last_seen: datetime


class TaskOut(BaseModel):
    id: int
    target_agent_id: str
    type: str
    status: str
    created_at: datetime


class ResultOut(BaseModel):
    id: int
    task_id: int
    agent_id: str
    status: str
    created_at: datetime
    output_json: Dict[str, Any]
