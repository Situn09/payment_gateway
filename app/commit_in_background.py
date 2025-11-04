import threading
from .database import SessionLocal
from .models import Transaction

def commit_in_background(transaction):
    db = SessionLocal()
    try:
        tx = Transaction(**transaction)
        db.add(tx)
        db.commit()
        print("Background commit success")
    except Exception as e:
        db.rollback()
        print("Background commit failed:", e)
    finally:
        db.close()
