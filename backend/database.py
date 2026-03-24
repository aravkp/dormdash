from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

SQLALCHEMY_DATABASE_URL = "sqlite:///./dormdash.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # ensure models module is imported so tables are registered on Base
    import models  # simple import (no package) — works when running from backend/
    Base.metadata.create_all(bind=engine)

    # Lightweight migration for existing SQLite DBs.
    with engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(deliveries)")).fetchall()
        col_names = {row[1] for row in cols}
        required_columns = [
            "order_from",
            "laundry_type",
            "laundry_drop_day",
            "laundry_drop_time",
            "laundry_pickup_days",
            "laundry_pickup_time",
            "mail_delivery_day",
            "mail_delivery_slot",
            "tuck_shop_location",
        ]
        for col in required_columns:
            if col not in col_names:
                conn.execute(text(f"ALTER TABLE deliveries ADD COLUMN {col} VARCHAR"))
        conn.commit()