import os
import shutil
import json
import time
import traceback
import sys
import logging
import paramiko
import argparse
import io
import uuid
from io import BytesIO
from tempfile import TemporaryDirectory, SpooledTemporaryFile
from PIL import Image
from fastapi import FastAPI, File, UploadFile,Request, Form, HTTPException # type: ignore
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from uuid import uuid4
from typing import Optional, Literal
from pathlib import Path
from datetime import datetime

from src.app.gl_convert_pdftoImage import pdf2ImageMethod
from src.app.gl_ocrService import processOcr
from src.app.gl_utilities import upload_to_sftp,convert_ndarray

from src.config.config import database
# from src.config.db.models import ocr_documents
from src.config.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(docs_url="/docs", redoc_url="/redoc")
# Path to your templates folder
templates = Jinja2Templates(directory="templates")
# Serve static files (CSS/JS) for Swagger UI
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "lib"), name="static")

# Ensure temp directory exists
TEMP_DIR = "app/temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


@app.on_event("startup")
async def startup():
    try:
        logger.info("glByte InHouse OCR Application is starting up...")
        init_db()
        logger.info("Database initialization completed")
        await database.connect()
        logger.info("Database connection established")
        logger.info("glByte InHouse OCR Application is Started Successfully...")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    logger.info("glByte InHouse OCR Application disconneted Successfully...")


# @app.get("/docs", include_in_schema=False)
# async def custom_swagger_ui_html():
#     return FileResponse("app/static/swagger-ui/index.html")

@app.get("/test", response_class=HTMLResponse)
async def test_endpoint():
    return {"message": "FastAPI is working!", "docs_url": "/docs", "redoc_url": "/redoc"}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# # ✅ Dummy POST to insert test row
@app.post("/test_db_insert")
async def test_db_insert():
    try:
        query = ocr_documents.insert().values(
            file_name="test_invoice.pdf",
            status="TEST_SUCCESS",
            creation_date=datetime.now()
        )
        inserted_id = await database.execute(query)
        return {"status": "Success", "inserted_id": inserted_id}
    except Exception as e:
        return {"status": "Failed", "error": str(e)}

@app.post("/ocr_process/")
async def ocr_process_file(
    file: UploadFile = File(...),
    doctype: Optional[Literal["INVOICE", "BANKSTMT"]] = Form(None)
    # doctype: Literal["invoice", "BANKSTMT"] = Form(...)
    # input_folder: Optional[str] = Form(None)
):
    try:
        # Create a unique filename
        uniqueId = str(uuid4())
        temp_dir = os.path.join(TEMP_DIR,uniqueId)
        start_time = datetime.now()
        # temp_file_name = f"{uuid4()}_{file.filename}"
        temp_file_name = file.filename
        temp_file_path = os.path.join(temp_dir, temp_file_name)
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        # Save file to temp folder
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # inserted_id = await database.execute(
        #     ocr_documents.insert().values(
        #         file_name=file.filename,
        #         actual_doc_type=doctype,
        #         creation_date=datetime.now(),
        #         process_id = uniqueId,
        #         doc_path = temp_file_name,
        #     )
        # )
        file_id = str(uuid.uuid4())
        print(f"Filename: {file.filename} and the file path {temp_file_path}")  # Print or store it for further use
        ocrObject = processOcr(temp_dir, doctype,temp_file_name,uniqueId)
        # ocrObject = processOcr_new(temp_dir, doctype,temp_file_name,uniqueId)
        cleaned_ocrObject = convert_ndarray(ocrObject)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # print(f'Data upload in the DB Successfully and id is {inserted_id}')
        shutil.rmtree(temp_dir)
        return {"status_code":200,"status":'Success',"data": cleaned_ocrObject}
    except Exception as e:
        # print(f"❌ Error during file processing: {e}")
        # return JSONResponse(status_code=500, content={"error": str(e)})
        exc_type, exc_obj, tb = sys.exc_info()
        fname = os.path.split(tb.tb_frame.f_code.co_filename)[1]
        line_no = tb.tb_lineno
        print(f"❌ Error during file processing: {e} (File: {fname}, Line: {line_no})")
        shutil.rmtree(temp_dir)
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"{e} (File: {fname}, Line: {line_no})"})

@app.post("/ocr_batch_process/")
async def ocr_batch_process(
    folder_path: str = Form(...),
    doctype: Literal["invoice", "BANKSTMT"] = Form(...)
):
    processed = []

    remote_folder = Path(folder_path)
    if not remote_folder.exists() or not remote_folder.is_dir():
        return {"error": "Invalid folder path"}

    # Supported file types
    supported_exts = [".pdf", ".jpg", ".jpeg", ".png"]

    for file in remote_folder.iterdir():
        if file.suffix.lower() in supported_exts and file.is_file():
            final_output = ocr_process_file(file, doctype)

            processed.append({
                "filename": file.name,
                "processId": final_output["processId"],
                "filePath": final_output["filePath"],
                "fileDir": final_output["fileDir"],
                "document_type": final_output["document_type"],
                "fileType": final_output["fileType"]
            })

    return {"processed": processed}

@app.post("/ocr_batch_process_sftp/")
async def ocr_batch_process_sftp(
    folder_path: str = Form(...),
    doctype: Literal["INVOICE", "BANKSTMT"] = Form(...)
):
    # Local file handling instead of SFTP
    processed = []

    try:
        # Check if folder exists locally
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return {"error": "Invalid folder path"}

        # List files in local directory
        remote_files = os.listdir(folder_path)
        supported_exts = [".pdf", ".jpg", ".jpeg", ".png"]

        for filename in remote_files:
            if any(filename.lower().endswith(ext) for ext in supported_exts):
                remote_file_path = os.path.join(folder_path, filename)
                try:
                    start_time = datetime.now()
                    # Read the file content into memory
                    with open(remote_file_path, "rb") as f:
                        content = f.read()

                    # Create a SpooledTemporaryFile and UploadFile wrapper
                    spooled_file = SpooledTemporaryFile()
                    spooled_file.write(content)
                    spooled_file.seek(0)

                    upload_file = UploadFile(filename=filename, file=spooled_file)

                    # ✅ Call your FastAPI OCR processor
                    final_output = await ocr_process_file(upload_file, doctype)
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    # Add to processed summary
                    print('review final_output and get the value    -> ', final_output)
                    processInfo = final_output["data"]
                    processed.append({
                        "filename": filename,
                        "processId": processInfo["processId"],
                        "filePath": processInfo["filePath"],
                        "fileDir": processInfo["fileDir"],
                        "document_type": processInfo["document_type"],
                        "fileType": processInfo["fileType"],
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "duration_seconds": duration
                    })

                except Exception as e:
                    print(f"❌ Error processing {filename}: {e}")

    except Exception as e:
        return {"error": str(e)}
    
    REMOTE_DIR = "/files/ocr_files"
    # Save results locally instead of uploading to SFTP
    json_str = json.dumps(processed, indent=4, default=convert_ndarray)
    json_bytes = json_str.encode("utf-8") # Encode to bytes
    local_file_name = f"bulk_processed_final.json" # Define the local file name and directory
    
    # Ensure directory exists
    os.makedirs(REMOTE_DIR, exist_ok=True)
    local_file_path = os.path.join(REMOTE_DIR, local_file_name)
    
    with open(local_file_path, "wb") as f:
        f.write(json_bytes)
    
    print(f"💾 Batch results saved locally: {local_file_path}")
    
    return {"processed": processed}


@app.post("/upload-fieldKeys-csv/")
async def upload_csv(file: UploadFile = File(...), document_type: Literal["INVOICE", "BANKSTMT"] = Form(...)):
    if document_type not in ["INVOICE", "BANKSTMT"]:
        raise HTTPException(status_code=400, detail="Invalid document_type. Must be 'INVOICE' or 'BANKSTMT'.")

    # Set the filename
    filename = "Invoice_allkeys.csv" if document_type == "INVOICE" else "Bankstmt_allkeys.csv"
    SFTP_UPLOAD_DIR = "/files/ocr_files/"
    
    # Read file content into memory
    content = await file.read()

    try:
        # Ensure directory exists locally
        os.makedirs(SFTP_UPLOAD_DIR, exist_ok=True)
        
        # Save file locally
        local_file_path = os.path.join(SFTP_UPLOAD_DIR, filename)
        with open(local_file_path, "wb") as f:
            f.write(content)

        print(f"💾 CSV file saved locally: {local_file_path}")
        return JSONResponse(content={"status": "success", "message": f"Uploaded as {filename}"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local Upload Failed: {e}")


############################################################
# Main Process 
############################################################

