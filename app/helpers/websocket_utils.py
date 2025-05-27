from abc import ABC, abstractmethod
from typing import Dict
from uuid import UUID

from fastapi import WebSocket
from schemas.queues import AvaiableItemResponse, NoItemsAvaiable
from schemas.websocket import WebsocketFailResponse, WebsocketSuccessResponse
from service.rpa.queue_services import QueueService


class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.queue_service: QueueService = QueueService()

    async def connect(self, worker_id: str, websocket: WebSocket):
        self.active_connections[worker_id] = websocket

    async def disconnect(self, worker_id: str):
        websocket = self.active_connections.pop(worker_id, None)
        if websocket and websocket.client_state.value != 3:  # 3 = CLOSED
            print(f"Closing connection with: {worker_id}")
            await websocket.close()

    def get_next_item(self, queue_name: str, worker_id: str):
        item = self.queue_service.get_next_item(queue_name, worker_id)

        if item is None:
            return NoItemsAvaiable()

        return AvaiableItemResponse(item=item)

    def mark_success(self, item_id: UUID):
        try:
            self.queue_service.mark_success(item_id)
        except Exception as e:
            raise e
        response = WebsocketSuccessResponse(item_id=str(item_id))
        return response.model_dump(mode="json")

    def mark_fail(self, data):
        try:
            self.queue_service.mark_fail(data)
        except Exception as e:
            raise e
        response = WebsocketFailResponse(item_id=str(data["item"]["id"]))
        return response.model_dump(mode="json")


class WebSocketContext:
    def __init__(self, websocket: WebSocket, data: dict, manager: WebSocketConnectionManager):
        self.websocket = websocket
        self.data = data
        self.manager = manager

    @property
    def error_msg(self) -> str:
        return self.data.get("item", {}).get("error_msg", "Unknown error")

    @property
    def get_stdout(self) -> str:
        return self.data.get("item", {}).get("stdout", "No stdout provided")

    @property
    def get_stderr(self) -> str:
        return self.data.get("item", {}).get("stderr", "No stderr provided")

    @property
    def queue_name(self) -> str:
        return self.data.get("queue_name", None)

    @property
    def worker_id(self) -> str:
        return self.data.get("worker_id", None)


class WebSocketAction(ABC):
    @abstractmethod
    async def execute(self, websocket: WebSocket, data: dict, manager: WebSocketConnectionManager):
        pass


class GetNextItemAction(WebSocketAction):
    async def execute(self, context: WebSocketContext):
        item = context.manager.get_next_item(context.queue_name, context.worker_id)
        await context.websocket.send_json(item.model_dump(mode="json"))


class MarkSuccessAction(WebSocketAction):
    async def execute(self, context: WebSocketContext):
        result = context.manager.mark_success(context.data)
        await context.websocket.send_json(result)


class MarkFailAction(WebSocketAction):
    async def execute(self, context: WebSocketContext):
        result = context.manager.mark_fail(context.data)
        await context.websocket.send_json(result)


ACTION_REGISTRY: Dict[str, WebSocketAction] = {
    "get_next": GetNextItemAction(),
    "mark_success": MarkSuccessAction(),
    "mark_fail": MarkFailAction(),
}
