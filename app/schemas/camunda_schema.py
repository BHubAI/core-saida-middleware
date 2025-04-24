from pydantic import BaseModel


class ProcessKeyRequest(BaseModel):
    process_key: str


class Event(BaseModel):
    event_type: str
    event_data: dict
