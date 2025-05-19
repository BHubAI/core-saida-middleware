from datetime import datetime
from uuid import UUID

from api.base.endpoints import BaseEndpoint
from api.deps import DBSession
from fastapi import HTTPException
from models.queue import Queue
from models.queue_item import QueueItem
from schemas.queues import QueueItemCreate, QueueItemOut


ROUTE_PREFIX = "/api/bhub"


# TODO: Move database operations to a dedicated service
class BHubQueuesEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["BHub"], prefix=ROUTE_PREFIX)

        @self.router.post("/queues/create/{queue_name}")
        def create_queue(queue_name: str, db: DBSession):
            # Verifica se já existe fila com esse nome
            existing = db.query(Queue).filter(Queue.name == queue_name).first()
            if existing:
                raise HTTPException(status_code=400, detail="Queue with this name already exists")

            new_queue = Queue(name=queue_name, description="", created_at=datetime.utcnow())

            db.add(new_queue)
            db.commit()
            db.refresh(new_queue)
            return new_queue

        @self.router.post("/queues/{queue_name}/items")
        def add_item(queue_name: str, item: QueueItemCreate, db: DBSession):
            queue = db.query(Queue).filter_by(name=queue_name).first()
            if not queue:
                raise HTTPException(status_code=404, detail="Queue not found")

            new_item = QueueItem(
                queue_id=queue.id,
                payload=item.payload,
                priority=item.priority,
                status="pending",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_item)
            db.commit()
            db.refresh(new_item)
            return new_item

        @self.router.get("/queues/{queue_name}/items")
        def get_items(queue_name: str, db: DBSession):
            queue = db.query(Queue).filter_by(name=queue_name).first()
            if not queue:
                raise HTTPException(status_code=404, detail="Queue not found")

            items = (
                db.query(QueueItem)
                .filter_by(queue_id=queue.id, status="pending")
                .order_by(QueueItem.priority.desc(), QueueItem.created_at)
                .all()
            )

            if not items:
                raise HTTPException(status_code=404, detail="No available item")
            return items

        @self.router.get("/queues/{queue_name}/next", response_model=QueueItemOut)
        def get_next_item(queue_name: str, worker_id: str, db: DBSession):
            queue = db.query(Queue).filter_by(name=queue_name).first()
            if not queue:
                raise HTTPException(status_code=404, detail="Queue not found")

            item = (
                db.query(QueueItem)
                .filter_by(queue_id=queue.id, status="pending")
                .order_by(QueueItem.priority.desc(), QueueItem.created_at)
                .with_for_update(skip_locked=True)
                .first()
            )

            if not item:
                raise HTTPException(status_code=404, detail="No available item")

            item.status = "in_progress"
            item.locked_by = worker_id
            item.locked_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(item)
            return item

        @self.router.post("/queues/items/{item_id}/success")
        def mark_success(item_id: UUID, db: DBSession):
            item = db.query(QueueItem).filter_by(id=item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            item.status = "successful"
            item.updated_at = datetime.utcnow()
            db.commit()
            return {"status": "ok"}

        @self.router.post("/queues/items/{item_id}/fail")
        def mark_fail(item_id: UUID, error: str, db: DBSession):
            item = db.query(QueueItem).filter_by(id=item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            item.attempts += 1
            item.error = error
            item.updated_at = datetime.utcnow()
            if item.attempts >= item.max_attempts:
                item.status = "failed"
            else:
                item.status = "pending"
                item.locked_by = None
                item.locked_at = None
            db.commit()
            return {"status": "ok"}
