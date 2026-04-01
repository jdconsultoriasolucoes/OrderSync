import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    res = conn.execute(text("SELECT NOW(), CURRENT_SETTING('TIMEZONE')")).first()
    print(f"DB NOW: {res[0]}")
    print(f"DB TIMEZONE: {res[1]}")

import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("America/Sao_Paulo")
print(f"Python NOW (Internal): {datetime.datetime.now()}")
print(f"Python NOW (Sao Paulo): {datetime.datetime.now(TZ)}")
