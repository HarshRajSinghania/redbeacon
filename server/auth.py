from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .crud import get_agent_by_token


ADMIN_HEADER = "X-Admin-Token"
AGENT_HEADER = "X-Agent-Token"


def require_admin(x_admin_token: str | None = Header(default=None, alias=ADMIN_HEADER)):
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
    return True


def require_agent(
    x_agent_token: str | None = Header(default=None, alias=AGENT_HEADER),
    db: Session = Depends(get_db),
):
    if not x_agent_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing agent token")
    agent = get_agent_by_token(db, x_agent_token)
    if not agent:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid agent token")
    return agent
