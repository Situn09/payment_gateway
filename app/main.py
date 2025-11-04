from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime
import os
import redis
from rq import Queue
import time
import threading
from .commit_in_background import commit_in_background


from .database import SessionLocal, engine, Base
from . import models, schemas
from .models import Transaction, TransactionStatus

# Create DB tables on startup if not present (simple for demo)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Payment Webhooks")

# Redis queue
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = redis.from_url(REDIS_URL)
queue = Queue(connection=redis_conn, default_timeout=600)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def health():
    return {"status": "HEALTHY", "current_time": datetime.utcnow().isoformat() + "Z"}

@app.post("/v1/webhooks/transactions", status_code=status.HTTP_202_ACCEPTED)
def receive_webhook(payload: schemas.WebhookPayload, request: Request, db: Session = Depends(get_db)):
    """
    Accepts webhook -> returns 202 immediately -> enqueues background job.
    Must respond quickly.
    """
    start = time.time()
    now = datetime.utcnow()
    print("start %.3fs", time.time() - start)
    # Try to insert a new record. If unique constraint fails, pick up existing.
    try:
        tx = Transaction(
            transaction_id=payload.transaction_id,
            source_account=payload.source_account,
            destination_account=payload.destination_account,
            amount=payload.amount,
            currency=payload.currency,
            status=TransactionStatus.PROCESSING,
            enqueued_at=now
        )
        db.add(tx)
        print("after add %.3fs", time.time() - start)
        # start = time.time()
        # db.commit()
        # ✅ async commit in separate session
        threading.Thread(
            target=commit_in_background,
            args=({
        "transaction_id": payload.transaction_id,
        "source_account": payload.source_account,
        "destination_account": payload.destination_account,
        "amount": payload.amount,
        "currency": payload.currency,
        "status": TransactionStatus.PROCESSING,
        "enqueued_at": now
    },),
            daemon=True
        ).start()
        print("after commit %.3fs", time.time() - start)
        start = time.time()
        # db.refresh(tx)
        # print("after refresh %.3fs", time.time() - start)
        start = time.time()
        # queue.enqueue("app.tasks.process_transaction", payload.transaction_id)
        # ✅ push job asynchronously in a thread, don't block response
        threading.Thread(
            target=lambda: queue.enqueue("app.tasks.process_transaction", payload.transaction_id),
            daemon=True
        ).start()
        print("after enqueue %.3fs", time.time() - start)
        # Enqueue background job
        # queue.enqueue("app.tasks.process_transaction", payload.transaction_id)
    except IntegrityError:
        db.rollback()
        # Another webhook already created this transaction; ensure we don't enqueue twice.
        existing = db.query(Transaction).filter_by(transaction_id=payload.transaction_id).first()
        if not existing:
            # unexpected — but return 202
            return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={})
        # If existing not processed and not enqueued, set enqueued_at and enqueue.
        # We use DB row-level lock to avoid races in workers.
        if existing.status != TransactionStatus.PROCESSED:
            # if enqueued_at is None -> enqueue; else ignore.
            if existing.enqueued_at is None:
                existing.enqueued_at = now
                db.add(existing)
                db.commit()
                queue.enqueue("app.tasks.process_transaction", payload.transaction_id)
        # else already processed -> nothing
    except Exception as e:
        db.rollback()
        # worst-case: still return 202 (to external provider) but log error (here we raise)
        raise HTTPException(status_code=500, detail="Internal error while accepting webhook")
    # per requirement, 202 with empty body is fine
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={})

@app.get("/v1/transactions/{transaction_id}", response_model=schemas.TransactionOut)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter_by(transaction_id=transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    # Convert numeric to float for Pydantic
    return tx
