from datetime import datetime
from enum import Enum

from models.base import BaseModel
from sqlmodel import JSON, Column, DateTime, Field


class RPAEventTypes(str, Enum):
    START = "start"
    FINISH = "finish"
    FINISH_WITH_ERROR = "finish_with_error"


class RPASource(str, Enum):
    MELIUS = "melius"
    UIPATH = "uipath"


class RPAEventLog(BaseModel, table=True):
    __tablename__: str = "rpa_event_log"

    process_id: str = Field(..., description="The key of camunda process")
    event_type: RPAEventTypes = Field(..., description="The type of the event")
    event_data: dict = Field(sa_column=Column(JSON), description="The data of the event")
    event_source: RPASource = Field(..., description="The source of the event")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False), default_factory=datetime.utcnow
    )

    def model_dump_as_csv(self):
        model_dump = [
            self.process_id,
            self.event_type.value,
            self.event_source.value,
        ]

        if self.event_type == RPAEventTypes.FINISH_WITH_ERROR:
            model_dump.append(self.event_data["error"])
            model_dump.append(self.event_data.get("response_content", ""))
        else:
            model_dump.append(self.event_data["baseOrigem"])
            model_dump.append(self.event_data["nomeCliente"])
            model_dump.append(self.event_data["documentoCliente"])
            model_dump.append(self.event_data["tipoTarefaRpa"])
            model_dump.append(self.event_data["idTarefaRPA"])

        model_dump.append(self.created_at.strftime("%Y-%m-%d %H:%M:%S"))

        return model_dump
