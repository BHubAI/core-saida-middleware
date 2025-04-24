from enum import Enum

from models.base import BaseModel
from sqlmodel import JSON, Column, Field


class ProcessEventTypes(str, Enum):
    START = "start"
    END = "end"
    START_ERROR = "start_error"
    SKIPPED = "skipped"


class ProcessEventLog(BaseModel, table=True):
    __tablename__: str = "process_event_log"

    process_id: str = Field(..., description="The key of the process")
    event_type: str = Field(..., description="The type of the event")
    event_data: dict = Field(sa_column=Column(JSON), description="The data of the event")
