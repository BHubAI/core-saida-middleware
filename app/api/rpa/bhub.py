from collections import defaultdict
from typing import Dict
from uuid import UUID

from api.base.endpoints import BaseEndpoint
from fastapi import HTTPException, Request
from schemas.queues import (
    AvaiableItems,
    ItemAddedToQueue,
    NoItemsAvaiable,
    QueueCreatedResponse,
    QueueItemCreate,
    QueueItemOut,
    QueueStatusResponse,
)
from service.rpa.queue_services import QueueService


ROUTE_PREFIX = "/api/bhub"
logs_per_task: Dict[str, list] = defaultdict(list)


class BHubQueuesEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["BHub"], prefix=ROUTE_PREFIX)
        self.queue_service = QueueService()

        @self.router.post("/queues/create/{queue_name}")
        def create_queue(queue_name: str, queue_description: str):
            response = self.queue_service.create_queue(queue_name, queue_description)
            return QueueCreatedResponse(queue_info=response)

        @self.router.post("/queues/{queue_name}/items")
        def add_item(queue_name: str, item: QueueItemCreate):
            response = self.queue_service.add_item(queue_name, item)
            return ItemAddedToQueue(
                item_status=response.status,
                priority=response.priority,
            )

        @self.router.get("/queues/{queue_name}/items")
        def get_pending_items(queue_name: str):
            items = self.queue_service.get_pending_items(queue_name)

            if not items:
                return NoItemsAvaiable()

            return AvaiableItems(items=items)

        @self.router.put("/queues/{queue_name}/toggle", response_model=QueueStatusResponse)
        def toggle_queue_status(queue_name: str):
            queue = self.queue_service.toggle_queue_status(queue_name)

            if queue is None:
                raise HTTPException(status_code=404, detail="Fila não encontrada")

            return QueueStatusResponse(
                queue_name=queue.name,
                is_active=queue.is_active,
                message=f"Fila {'ativada' if queue.is_active else 'pausada'} com sucesso.",
            )

        # Moved to Websocket
        @self.router.get("/queues/{queue_name}/next", response_model=QueueItemOut)
        def get_next_item(queue_name: str, worker_id: str):
            return self.queue_service.get_next_item(queue_name, worker_id)

        # Moved to Websocket
        @self.router.post("/queues/items/{item_id}/success")
        def mark_success(item_id: UUID):
            try:
                self.queue_service.mark_success(item_id)
            except Exception as e:
                raise e
            return {"status": "ok"}

        # Moved to Websocket
        @self.router.post("/queues/items/{item_id}/fail")
        def mark_fail(item_id: UUID, error: str):
            try:
                self.queue_service.mark_fail(item_id, error)
            except Exception as e:
                raise e
            return {"status": "ok"}


class BHubLogsEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["BHub", "Logs"], prefix=ROUTE_PREFIX)

        @self.router.post("/logs/save/{item_id}")
        async def save_log(item_id: str, request: Request):
            data = await request.json()
            logs_per_task[item_id].append(data)
            return {"status": "ok"}

        @self.router.get("/logs/retrieve/{item_id}")
        def get_logs(item_id: str):
            return logs_per_task.get(item_id, [])

        @self.router.get("/logs/formatted/{item_id}")
        def get_formatted_logs(item_id: str):
            return [
                f"[{log['task_id']}] [{log['level']}] [{log['timestamp']}] {log['message']}"
                for log in logs_per_task.get(item_id, [])
            ]
