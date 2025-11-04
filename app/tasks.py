# This file is imported by RQ worker. Keep logic here.
import time
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models import Transaction, TransactionStatus

def process_transaction(transaction_id: str):
    """Background job: simulate external API call then mark as PROCESSED."""
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter_by(transaction_id=transaction_id).with_for_update().first()
        if not tx:
            # nothing to do
            return

        # If already processed, skip
        if tx.status == TransactionStatus.PROCESSED:
            return

        # Simulate long-running work (external API call)
        time.sleep(30)  # requirement: 30-second delay to simulate external API

        # Update transaction as processed
        tx.status = TransactionStatus.PROCESSED
        tx.processed_at = datetime.utcnow()
        db.add(tx)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        # mark as FAILED so operator can inspect
        try:
            tx = db.query(Transaction).filter_by(transaction_id=transaction_id).first()
            if tx:
                tx.status = TransactionStatus.FAILED
                tx.last_error = str(e)
                db.add(tx)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()
