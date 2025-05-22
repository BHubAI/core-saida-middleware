from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from models import Queue, QueueItem
from schemas.queues import QueueItemCreate
from sqlalchemy.orm import Session


class QueueService:
    @staticmethod
    def create_queue(queue_name: str, queue_description: str, db: Session):
        if db.query(Queue).filter(Queue.name == queue_name).first():
            raise HTTPException(status_code=400, detail="Queue with this name already exists")
        new_queue = Queue(name=queue_name, description=queue_description, created_at=datetime.utcnow())
        db.add(new_queue)
        db.commit()
        db.refresh(new_queue)
        return new_queue

    @staticmethod
    def add_item(queue_name: str, item_data: QueueItemCreate, db: Session):
        queue = db.query(Queue).filter_by(name=queue_name).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")
        new_item = QueueItem(
            queue_id=queue.id,
            payload=item_data.payload,
            priority=item_data.priority,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item

    @staticmethod
    def get_pending_items(queue_name: str, db: Session):
        queue = db.query(Queue).filter_by(name=queue_name).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")
        items = (
            db.query(QueueItem)
            .filter_by(queue_id=queue.id, status="pending")
            .order_by(QueueItem.priority.desc(), QueueItem.created_at)
            .all()
        )
        return items

    @staticmethod
    def get_next_item(queue_name: str, worker_id: str, db: Session):
        queue = db.query(Queue).filter_by(name=queue_name).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")
        item = (
            db.query(QueueItem)
            .filter_by(queue_id=queue.id, status="pending", locked_by=None)
            .order_by(QueueItem.priority.desc(), QueueItem.created_at)
            .with_for_update(skip_locked=True)
            .first()
        )
        if not item:
            return None

        item.status = "running"
        item.locked_by = worker_id
        item.locked_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def mark_success(item_id: UUID, db: Session):
        item = db.query(QueueItem).filter_by(id=item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item.status = "success"
        item.updated_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def mark_fail(item_id: UUID, error: str, db: Session):
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
