from unicodedata import numeric
from sqlalchemy import Table, Column, Integer, String, DateTime, Text, Numeric
from ..config import metadata, database
from datetime import datetime

# from init_db import init_db

# ocr_documents = Table(
#     "ocr_documents", metadata,
#     Column("id", Integer, primary_key=True),
#     Column("process", String(100)),
#     Column("status", String(50)),
#     Column("data", Text),
#     Column("file_name", String(255)),
#     Column("actual_doc_type", String(100)),
#     Column("identified_doc_type", String(100)),
#     Column("objectType", String(100)),
#     Column("doc_gen_type", String(100)),
#     Column("doc_sub_type", String(100)),
#     Column("file_type", String(50)),
#     Column("tenant_id", Integer),
#     Column("process_id", String(100)),
#     Column("number_of_pages", Integer),
#     Column("stage", String(100)),
#     Column("created_by", String(100)),
#     Column("creation_date", DateTime, default=datetime.utcnow),
#     Column("last_updated_by", String(100)),
#     Column("last_updated_date", DateTime, default=datetime.utcnow),
#     Column("id_for_display", String(100)),
#     Column("doc_path", String(255)),
#     Column("message", Text),
#     Column("ai_object", Text),
#     Column("duration", Numeric(10, 2)),
#     schema="ocr_apidb"
# )

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