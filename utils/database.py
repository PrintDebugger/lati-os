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
                        id BIGSERIAL PRIMARY KEY,
                        wallet INTEGER DEFAULT 10000,
                        bank INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1,
                        exp INTEGER DEFAULT 0
                    );
                """)
                conn.commit()
        log(f"Connected to PostgreSQL database '{PGDATABASE}' at {PGHOST}:{PGPORT}")
    
    except Exception as e:
        log(f"❌ ERROR: Could not connect to PostgreSQL database:\n{str(e)}")
        raise

def execute_query(query, params=(), fetch=None):
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
                
                # For SELECT queries, return the result
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                
                # For INSERT, UPDATE, DELETE, return True if any rows were affected
                if cursor.rowcount > 0:
                    return True
                else:
                    return False
    except Exception as e:
        from utils import log
        log(f"❌ ERROR: In 'execute_query':\n{str(e)}")
        raise