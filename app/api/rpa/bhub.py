from collections import defaultdict
from typing import Dict

from api.base.endpoints import BaseEndpoint
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from schemas.queues import (
    AvaiableItemsResponse,
    ItemAddedToQueue,
    NoItemsAvaiableResponse,
    QueueCreatedResponse,
    QueueDeletedResponse,
    QueueItemCreate,
    QueueStatusResponse,
)
from service.rpa.queue_services import QueueService


class BHubRPAQueuesEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["BHub"], prefix="/api/bhub")
        self.queue_service = QueueService()

        @self.router.post("/queues/create/{queue_name}")
        def create_queue(queue_name: str, queue_description: str):
            response = self.queue_service.create_queue(queue_name, queue_description)
            return QueueCreatedResponse(queue_info=response)

        @self.router.delete("/queues/delete/{queue_id}")
        def delete_queue(queue_id: int):
            self.queue_service.delete_queue(queue_id)

            return QueueDeletedResponse(queue_id=queue_id)

        @self.router.post("/queues/{queue_name}/add/item")
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
                return NoItemsAvaiableResponse()

            return AvaiableItemsResponse(items=items)

        @self.router.get("/queues/{queue_name}/retired")
        def get_retired_items(queue_name: str):
            items = self.queue_service.get_retired_items(queue_name)

            if not items:
                return NoItemsAvaiableResponse(message="No items in RETIRED state at the moment")

            return AvaiableItemsResponse(items=items)

        @self.router.put("/queues/{queue_name}/toggle", response_model=QueueStatusResponse)
        def toggle_queue_status(queue_name: str):
            queue = self.queue_service.toggle_queue_status(queue_name)

            if queue is None:
                raise HTTPException(status_code=404, detail="Fila não encontrada")

            return QueueStatusResponse(
                queue_name=queue.name,
                is_active=queue.is_active,
                message=f"Queue status: {'active' if queue.is_active else 'paused'}.",
            )


class BHubRPALogsEndpoint(BaseEndpoint):
    """NOTE: this endpoint will be removed soon and a new way to handle this operation will be applied"""

    def __init__(self):
        super().__init__(tags=["BHub", "Logs"], prefix="/api/bhub/logs")
        self.logs_per_task: Dict[str, list] = defaultdict(list)

        @self.router.post("/save/{item_id}")
        async def save_log(item_id: str, request: Request):
            data = await request.json()
            self.logs_per_task[item_id].append(data)
            return {"status": "ok"}

        @self.router.get("/retrieve/{item_id}")
        def get_logs(item_id: str):
            return self.logs_per_task.get(item_id, [])

        @self.router.get("/formatted/{item_id}", response_class=HTMLResponse)
        def get_formatted_logs(item_id: str):
            logs = self.logs_per_task.get(item_id, [])

            if not logs:
                return HTMLResponse(content=f"<h2>No logs found for item_id: {item_id}</h2>", status_code=404)

            html_content = f"<h2>Logs for Item ID: {item_id}</h2>"

            for log in logs:
                pre = """
                    <pre style='
                        background:#f4f4f4;
                        padding:10px;
                        border-radius:5px;
                        border-style:solid;
                        border-color:black;
                    '>
                """
                line = pre + f"[{log['task_id']}] [{log['level']}] [{log['timestamp']}] {log['message']}</pre>"
                html_content += line

            return HTMLResponse(content=html_content, status_code=200)
