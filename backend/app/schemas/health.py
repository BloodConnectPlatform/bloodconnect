from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    database: str
    environment: str
    version: str
    timestamp: str
    error: Optional[str] = None
