import atexit
import os
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool


load_dotenv()

PGHOST = os.environ['PGHOST']
PGUSER = os.environ['PGUSER']
PGPASSWORD = os.environ['PGPASSWORD']
PGDATABASE = os.environ['PGDATABASE']
PGPORT = os.environ['PGPORT']


#   Initialise the connection pool
pool = ConnectionPool(
    conninfo = f"host={PGHOST} user={PGUSER} password={PGPASSWORD} dbname={PGDATABASE} port={PGPORT}",
    min_size = 1,
    max_size = 10
)

#   Register cleanup
atexit.register(pool.close)


def initialise_db():
    
    # Connect to PostgreSQL
    from utils import logger
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                # Create table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGSERIAL PRIMARY KEY,
                        wallet INTEGER DEFAULT 10000,
                        bank INTEGER DEFAULT 0,
                        bankBonus INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1,
                        exp INTEGER DEFAULT 0,
                        items JSONB DEFAULT '{}'::jsonb,
                        activeItems JSONB DEFAULT '{}'::jsonb
                    );
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS bankBonus INTEGER DEFAULT 0;
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS items JSONB DEFAULT '{}'::jsonb;
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS activeItems JSONB DEFAULT '{}'::jsonb;
                """)
                conn.commit()
        logger.info(f"Connected to PostgreSQL database '{PGDATABASE}' at {PGHOST}:{PGPORT}")   
    except Exception:
        logger.critical(f"Could not connect to PostgreSQL database")


def execute_query(query, params=(), fetch=None):
    from utils import logger
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                
                # For SELECT queries, return the result
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                # For INSERT, UPDATE, DELETE, return True if any rows were affected
                else:
                    return cursor.rowcount
    except Exception:
        logger.exception("Exception in database query")