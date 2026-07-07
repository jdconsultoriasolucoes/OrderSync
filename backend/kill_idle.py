import os
from sqlalchemy import text
from database import SessionLocal

def run():
    db = SessionLocal()
    try:
        sql = text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' OR state = 'idle in transaction (aborted)'")
        res = db.execute(sql).fetchall()
        print(f"Terminated {len(res)} idle transactions.")
    finally:
        db.close()

if __name__ == '__main__':
    run()
