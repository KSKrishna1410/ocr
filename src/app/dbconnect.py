from src.config.config import database
from src.config.db.init_db import init_db

from src.config.db.models import ocr_documents  # your table
import asyncio

async def fetch_ocr_documents(process_id):
    query = select(ocr_documents).where(ocr_documents.c.process_id == process_id)
    # query = "SELECT * FROM ocr_documents WHERE process_id = :process_id"
    # values = {"process_id": process_id}
    rows = await database.fetch_all(query)
    return [dict(row) for row in rows]

# Run the async function
if __name__ == "__main__":
    process_id = "12345"  # example
    result = asyncio.run(fetch_ocr_documents(process_id))
    print(result)

