from abc import ABC, abstractmethod
from typing import Dict

from fastapi import WebSocket
from schemas.queues import AvaiableItemResponse, NoItemsAvaiableResponse
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
            return NoItemsAvaiableResponse()

        return AvaiableItemResponse(item=item)

    def mark_success(self, data: dict):
        self.queue_service.mark_success(data)
        response = WebsocketSuccessResponse(item_id=str(data["item"]["id"]))

        return response.model_dump(mode="json")

    def mark_fail(self, data: dict):
        self.queue_service.mark_fail(data)
        response = WebsocketFailResponse(item_id=str(data["item"]["id"]))

        return response.model_dump(mode="json")


class WebSocketContext:
    def __init__(self, websocket: WebSocket, data: dict, manager: WebSocketConnectionManager):
        self.websocket = websocket
        self.data = data
        self.manager = manager

    @property
    def queue_name(self) -> str:
        return self.data.get("queue_name", "")

    @property
    def worker_id(self) -> str:
        return self.data.get("worker_id", "")


class WebSocketAction(ABC):
    @abstractmethod
    async def execute(self, context: WebSocketContext):
        raise NotImplementedError()


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
