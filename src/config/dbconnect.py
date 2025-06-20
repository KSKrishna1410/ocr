from config import database
from db.init_db import init_db

# from db.models import ocr_documents  # your table
import asyncio

async def fetch_ocr_documents(docType):
    await database.connect()
    # query = select(ocr_documents).where(ocr_documents.c.docType == docType)
    query = """
        SELECT 
            tfcd.field_name, 
            tfk.key, 
            tfcd.data_type, 
            tfcd.field_type 
        FROM 
            t_icr_field_capture_data tfcd, 
            t_icr_field_keys tfk 
        WHERE 
            tfcd.id = tfk.field_id 
            AND tfcd.tenant_id = -1 
            AND LOWER(tfcd.doc_type) = LOWER(:docType) 
        ORDER BY 
            tfcd.field_name
    """
    values = {"docType": docType}
    print(query)
    rows = await database.fetch_all(query=query, values=values)
    await database.disconnect()
    return [dict(row) for row in rows]

# Run the async function
if __name__ == "__main__":
    docType = 'invoice'  # example
    result = asyncio.run(fetch_ocr_documents(docType))
    print(result)

