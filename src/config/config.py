# Install dependencies
# pip install sqlalchemy databases asyncpg psycopg2-binary

# -------------------- db/config.py --------------------
import os
from databases import Database
from sqlalchemy import MetaData

# Use environment variable for database URL, fallback to Docker container
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://nekkanti:nekkanti_pass@db:5432/nekkanti_db"
)

database = Database(DATABASE_URL)
metadata = MetaData()