import pydantic


class Event(pydantic.BaseModel):
    """Event"""
    name: str
    data: dict