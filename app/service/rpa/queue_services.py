from datetime import datetime

from api.deps import DBSession, get_session
from fastapi import HTTPException
from models import Queue, QueueItem
from schemas.queues import QueueItemCreate, RPAStatus


class QueueService:
    def __init__(self):
        session_gen = get_session()
        self.db: DBSession = next(session_gen)

    def create_queue(self, queue_name: str, queue_description: str):
        if self.db.query(Queue).filter(Queue.name == queue_name).first():
            raise HTTPException(status_code=400, detail="Queue with this name already exists")

        new_queue = Queue(name=queue_name, description=queue_description, created_at=datetime.utcnow())
        self.db.add(new_queue)
        self.db.commit()
        self.db.refresh(new_queue)
        return new_queue

    def delete_queue(self, queue_id: int):
        queue = self.db.query(Queue).filter_by(id=queue_id).first()

        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        self.db.delete(queue)
        self.db.commit()

    def add_item(self, queue_name: str, item_data: QueueItemCreate):
        queue = self.db.query(Queue).filter_by(name=queue_name).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        new_item = QueueItem(
            queue_id=queue.id,
            payload=item_data.payload,
            priority=item_data.priority,
            status=RPAStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(new_item)
        self.db.commit()
        self.db.refresh(new_item)
        return new_item

    def get_pending_items(self, queue_name: str):
        queue = self.db.query(Queue).filter_by(name=queue_name).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        items = (
            self.db.query(QueueItem)
            .filter_by(queue_id=queue.id, status=RPAStatus.PENDING)
            .order_by(QueueItem.priority.desc(), QueueItem.created_at)
            .all()
        )
        return items

    def get_retired_items(self, queue_name=None):
        query = self.db.query(QueueItem).filter_by(status=RPAStatus.RETIRED)

        if queue_name:
            queue = self.db.query(Queue).filter_by(name=queue_name.strip()).first()
            if not queue:
                raise HTTPException(status_code=404, detail="Queue not found")
            query = query.filter(QueueItem.queue_id == queue.id)

        items = query.order_by(QueueItem.priority.desc(), QueueItem.created_at).all()
        return items

    def get_next_item(self, queue_name: str, worker_id: str):
        queue = self.db.query(Queue).filter_by(name=queue_name).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        if not queue.is_active:
            raise Exception(f"Queue '{queue_name}' está pausada")

        item = (
            self.db.query(QueueItem)
            .filter_by(queue_id=queue.id, status=RPAStatus.PENDING)
            .order_by(QueueItem.priority.desc(), QueueItem.created_at)
            .with_for_update(skip_locked=True)
            .first()
        )

        if item:
            item.status = RPAStatus.RUNNING
            item.locked_by = worker_id
            self.db.commit()
            self.db.refresh(item)

        return item

    def mark_success(self, data: dict):
        item = self.db.query(QueueItem).filter_by(id=data["item"]["id"]).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item.status = RPAStatus.SUCCESS
        item.updated_at = datetime.utcnow()
        item.started_at = data["started_at"]
        item.finished_at = data["finished_at"]
        self.db.commit()

    def mark_fail(self, data: dict):
        item = self.db.query(QueueItem).filter_by(id=data["item"]["id"]).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        item.attempts += 1
        item.error = data["stderr"]
        item.updated_at = datetime.utcnow()
        item.started_at = data["started_at"]
        item.finished_at = data["finished_at"]

        if item.attempts >= item.max_attempts:
            item.status = RPAStatus.FAILED
        if data["exception_type"] == "BusinessException":
            item.status = RPAStatus.RETIRED
        else:
            item.status = RPAStatus.PENDING
            item.locked_by = None
            item.locked_at = None

        self.db.commit()

    def toggle_queue_status(self, queue_name: str):
        queue = self.db.query(Queue).filter_by(name=queue_name).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        queue.is_active = not queue.is_active
        self.db.commit()
        self.db.refresh(queue)
        return queue
