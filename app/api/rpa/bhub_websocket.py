import json
from typing import Dict
from uuid import UUID

from api.base.endpoints import BaseEndpoint
from api.deps import get_session
from fastapi import WebSocket, WebSocketDisconnect
from schemas.queues import AvaiableItemResponse, NoItemsAvaiable
from schemas.websocket import WebsocketFailResponse, WebsocketSuccessResponse
from service.rpa.queue_services import QueueService


ROUTE_PREFIX = "/api/ws"


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, worker_id: str, websocket: WebSocket):
        self.active_connections[worker_id] = websocket

    async def disconnect(self, worker_id: str):
        websocket = self.active_connections.pop(worker_id, None)
        if websocket and websocket.client_state.value != 3:  # 3 = CLOSED
            await websocket.close()

    def get_next_item(self, queue_name: str, worker_id: str, db):
        item = QueueService.get_next_item(queue_name, worker_id, db)

        if item is None:
            return NoItemsAvaiable()

        return AvaiableItemResponse(item=item)

    def mark_success(self, item_id: UUID, db):
        try:
            QueueService.mark_success(item_id, db)
        except Exception as e:
            raise e
        return WebsocketSuccessResponse(item_id=str(item_id))

    def mark_fail(self, item_id: UUID, error: str, db):
        try:
            QueueService.mark_fail(item_id, error, db)
        except Exception as e:
            raise e
        return WebsocketFailResponse(item_id=str(item_id))


class BHubWebSocket(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["BHub", "WebSocket"], prefix=ROUTE_PREFIX)
        self.manager = ConnectionManager()

        @self.router.websocket("/worker/{queue_name}")
        async def worker_ws(websocket: WebSocket, queue_name: str):
            await websocket.accept()
            session_gen = get_session()
            db = next(session_gen)

            try:
                while True:
                    first_message = await websocket.receive_text()
                    print(f"Mensagem recebida: {first_message}")
                    first_data = json.loads(first_message)

                    worker_id = str(first_data.get("worker_id"))
                    action = str(first_data.get("action"))
                    data = first_data.get("data", {})

                    # await self.manager.connect(worker_id, websocket)
                    if action == "get_next":
                        try:
                            print("Enviando o item para processamento")
                            item = self.manager.get_next_item(queue_name, worker_id, db)
                            await websocket.send_json(item.model_dump(mode="json"))
                        except Exception as e:
                            await websocket.send_json({"error": str(e)})

                    elif action == "mark_success":
                        if data is None:
                            raise Exception("No data provided error")
                        try:
                            item_id = UUID(data.get("item_id"))
                            result = self.manager.mark_success(item_id, db)
                            await websocket.send_json(result)
                        except Exception as e:
                            await websocket.send_json({"error": str(e)})

                    elif action == "mark_fail":
                        if data is None:
                            raise Exception("No data provided error")
                        try:
                            item_id = UUID(data.get("item_id"))
                            error_msg = data.get("error", "Unknown error")
                            result = self.manager.mark_fail(item_id, error_msg, db)
                            await websocket.send_json(result)
                        except Exception as e:
                            await websocket.send_json({"error": str(e)})

            except WebSocketDisconnect:
                self.manager.disconnect(worker_id)
            finally:
                try:
                    next(session_gen)
                except StopIteration:
                    pass
