#   Fetch data from the database.

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.environ['DB_FILEPATH']

def initialise_db():
    from utils import log
    if DB_FILE is None:
        raise ValueError("environment key DB_FILEPATH is not set")
        return

    if not os.path.exists(DB_FILE):
        log("⚠️ WARNING: Creating database \"userdata.db\"")

    with sqlite3.connect(DB_FILE) as db:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                wallet INTEGER DEFAULT 10000,
                bank INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0
            )
        """)
        db.commit()
    
    log("Connected to database \"{0}\"".format(DB_FILE))

def execute_query(query, params=()):
    with sqlite3.connect(DB_FILE) as db:
        cursor = db.cursor()

        try:
            cursor.execute(query, params)
            db.commit()
            return cursor
        except sqlite3.OperationalError as e:
            from utils import log
            log("❌ ERROR: In \"execute_query\"")
            raise RuntimeError("Database Error: {0}".format(e)) from e
