import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

PGHOST = os.environ['PGHOST']
PGUSER = os.environ['PGUSER']
PGPASSWORD = os.environ['PGPASSWORD']
PGDATABASE = os.environ['PGDATABASE']
PGPORT = os.environ['PGPORT']

def initialise_db():
    from utils import log
    
    # Connect to PostgreSQL
    try:
        with psycopg.connect(
            host=PGHOST,
            user=PGUSER,
            password=PGPASSWORD,
            dbname=PGDATABASE,
            port=PGPORT
        ) as conn:
            with conn.cursor() as cursor:
                # Create table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name TEXT,
                        wallet INTEGER DEFAULT 10000,
                        bank INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1,
                        exp INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
                return cursor
        log("Connected to PostgreSQL database \"{0}\"".format(PGDATABASE))
    
    except Exception as e:
        log(f"❌ ERROR: Could not connect to PostgreSQL database: {e}")
        raise

def execute_query(query, params=()):
    try:
        with psycopg.connect(
            host=PGHOST,
            user=PGUSER,
            password=PGPASSWORD,
            dbname=PGDATABASE,
            port=PGPORT
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.fetchall()
    except Exception as e:
        from utils import log
        log("❌ ERROR: In \"execute_query\"\n{0}".format(e))