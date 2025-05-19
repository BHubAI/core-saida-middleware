from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class QueueItemCreate(BaseModel):
    payload: dict
    priority: Optional[int] = 0


class QueueItemOut(BaseModel):
    id: UUID
    payload: Any
    status: str

    class Config:
        orm_mode = True
