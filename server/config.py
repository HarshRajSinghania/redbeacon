from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # Admin token for creating tasks and listing data via API docs/CLI
    admin_token: str = Field(default="changeme-admin")
    # SQLite database path (relative to project root by default)
    db_path: str = Field(default=str(Path(__file__).resolve().parents[1] / "c2.db"))
    # Server bind host/port
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)


settings = Settings()
