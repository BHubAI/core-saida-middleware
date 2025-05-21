from collections import defaultdict
from typing import Dict
from uuid import UUID

from api.base.endpoints import BaseEndpoint
from api.deps import DBSession
from fastapi import Request
from schemas.queues import (
    AvaiableItems,
    ItemAddedToQueue,
    NoItemsAvaiable,
    QueueCreatedResponse,
    QueueItemCreate,
    QueueItemOut,
)
from service.rpa.queue_services import QueueService


ROUTE_PREFIX = "/api/bhub"
logs_by_task: Dict[str, list] = defaultdict(list)


class BHubQueuesEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["BHub"], prefix=ROUTE_PREFIX)

        @self.router.post("/queues/create/{queue_name}")
        def create_queue(queue_name: str, queue_description: str, db: DBSession):
            response = QueueService.create_queue(queue_name, queue_description, db)
            return QueueCreatedResponse(queue_info=response)

        @self.router.post("/queues/{queue_name}/items")
        def add_item(queue_name: str, item: QueueItemCreate, db: DBSession):
            response = QueueService.add_item(queue_name, item, db)
            return ItemAddedToQueue(
                item_status=response.status,
                priority=response.priority,
            )

        @self.router.get("/queues/{queue_name}/items")
        def get_items(queue_name: str, db: DBSession):
            items = QueueService.get_pending_items(queue_name, db)

            if not items:
                return NoItemsAvaiable()

            return AvaiableItems(items=items)

        # Moved to Websocket
        @self.router.get("/queues/{queue_name}/next", response_model=QueueItemOut)
        def get_next_item(queue_name: str, worker_id: str, db: DBSession):
            return QueueService.get_next_item(queue_name, worker_id, db)

        # Moved to Websocket
        @self.router.post("/queues/items/{item_id}/success")
        def mark_success(item_id: UUID, db: DBSession):
            try:
                QueueService.mark_success(item_id, db)
            except Exception as e:
                raise e
            return {"status": "ok"}

        # Moved to Websocket
        @self.router.post("/queues/items/{item_id}/fail")
        def mark_fail(item_id: UUID, error: str, db: DBSession):
            try:
                QueueService.mark_fail(item_id, error, db)
            except Exception as e:
                raise e
            return {"status": "ok"}


class BHubLogsEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["BHub", "Logs"], prefix=ROUTE_PREFIX)

        @self.router.post("/logs/save/{item_id}")
        async def save_log(item_id: str, request: Request):
            data = await request.json()
            logs_by_task[item_id].append(data)
            return {"status": "ok"}

        @self.router.get("/logs/retrieve/{item_id}")
        def get_logs(item_id: str):
            return logs_by_task.get(item_id, [])

        @self.router.get("/logs/formatted/{item_id}")
        def get_formatted_logs(item_id: str):
            return [
                f"{log['task_id']} {log['level']} {log['timestamp']} {log['message']}"
                for log in logs_by_task.get(item_id, [])
            ]
