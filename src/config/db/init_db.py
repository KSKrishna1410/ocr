from sqlalchemy import create_engine
from ..config import DATABASE_URL, metadata

# from sqlalchemy import MetaData

# DATABASE_URL = (
#     "postgresql+asyncpg://ocr_appdb:uat2app@192.168.0.134:5434/ocr_appdb"
#     "?options=-csearch_path%3Docr_appdb"
# )

# database = Database(DATABASE_URL)
# metadata = MetaData()

def init_db():
    engine = create_engine(DATABASE_URL.replace("+asyncpg", ""))  # use psycopg2 for DDL
    metadata.create_all(engine)