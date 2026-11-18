from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added after a database was first created. create_all() only creates missing tables, so an existing
# database (for example the hosted one) gets these added at start-up. Safe to run every time.
LATER_COLUMNS = [("vendor_applications", "delivery_partners", "INTEGER")]


def ensure_columns():
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, column, sql_type in LATER_COLUMNS:
            if table in inspector.get_table_names() and column not in {c["name"] for c in inspector.get_columns(table)}:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))
