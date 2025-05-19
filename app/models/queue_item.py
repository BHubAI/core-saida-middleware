from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Integer
from sqlmodel import Field, SQLModel


class QueueItem(SQLModel, table=True):
    __tablename__ = "queue_item"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    queue_id: int = Field(foreign_key="queue.id")

    status: str = Field(..., description="Status of the item: pending, in_progress, etc.")
    payload: dict = Field(..., sa_column=Column(JSON))

    priority: int = Field(default=0, sa_column=Column(Integer))
    attempts: int = Field(default=0, sa_column=Column(Integer))
    max_attempts: int = Field(default=3, sa_column=Column(Integer))

    error: Optional[str] = Field(default=None, description="Error message if failed")
    locked_by: Optional[str] = Field(default=None, description="Worker that locked the item")
    locked_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
