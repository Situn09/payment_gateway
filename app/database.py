import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/postgres")

# engine = create_engine(DATABASE_URL, pool_pre_ping=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # check stale connections
    pool_size=10,            # maintain 10 open connections
    max_overflow=20,         # allow bursts
    pool_recycle=1800,       # recycle every 30 min
    pool_timeout=30,         # wait up to 30s for a connection
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
