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

from uuid import uuid4
from typing import Optional, Literal
from pathlib import Path
from datetime import datetime

from src.gl_convert_pdftoImage import pdf2ImageMethod
from src.gl_ocrService import processOcr
from src.gl_utilities import upload_to_sftp,convert_ndarray



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(docs_url=None, redoc_url=None)

# Serve static files (CSS/JS) for Swagger UI
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "lib"), name="static")

# Serve custom Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return FileResponse("app/static/swagger-ui/index.html")

# Path to your templates folder
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    logger.info("glByte InHouse OCR Application is starting up...")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ensure temp directory exists
TEMP_DIR = "app/temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

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
        # temp_file_name = f"{uuid4()}_{file.filename}"
        temp_file_name = file.filename
        temp_file_path = os.path.join(temp_dir, temp_file_name)
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        # Save file to temp folder
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # file_id = str(uuid.uuid4())
        print(f"Filename: {file.filename} and the file path {temp_file_path}")  # Print or store it for further use
        ocrObject = processOcr(temp_dir, doctype,temp_file_name,uniqueId)
        # ocrObject = processOcr_new(temp_dir, doctype,temp_file_name,uniqueId)
        cleaned_ocrObject = convert_ndarray(ocrObject)
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
    # SFTP Config
    SFTP_HOST = os.getenv("SFTP_HOST")
    SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
    SFTP_USERNAME = os.getenv("SFTP_USERNAME")
    SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")

    processed = []

    try:
        # Connect to SFTP
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Verify folder exists
        try:
            sftp.chdir(folder_path)
        except FileNotFoundError:
            return {"error": "Invalid folder path"}

        # List files in remote directory
        remote_files = sftp.listdir(folder_path)
        supported_exts = [".pdf", ".jpg", ".jpeg", ".png"]

        for filename in remote_files:
            if any(filename.lower().endswith(ext) for ext in supported_exts):
                remote_file_path = f"{folder_path}/{filename}"
                try:
                    # Download file to temp directory
                    with TemporaryDirectory() as tmp_file:
                        tmp_path = Path(tmp_file) / filename
                        sftp.get(remote_file_path, str(tmp_path))
                        start_time = datetime.now()
                        # Read the file content into memory
                        with open(tmp_path, "rb") as f:
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

                finally:
                    # 🧹 Clean up temporary file        
                    if tmp_path.exists():
                        tmp_path.unlink()

        sftp.close()
        transport.close()

    except Exception as e:
        return {"error": str(e)}
    
    REMOTE_DIR = "/files/ocr_files"
    # Upload to SFTP using your common method
    json_str = json.dumps(processed, indent=4, default=convert_ndarray)
    json_bytes = json_str.encode("utf-8") # Encode to bytes
    remote_file_name = f"bulk_processed_final.json" # Define the remote file name and directory
    upload_to_sftp(json_bytes, remote_file_name, REMOTE_DIR)
    return {"processed": processed}


@app.post("/upload-fieldKeys-csv/")
async def upload_csv(file: UploadFile = File(...), document_type: Literal["INVOICE", "BANKSTMT"] = Form(...)):
    if document_type not in ["INVOICE", "BANKSTMT"]:
        raise HTTPException(status_code=400, detail="Invalid document_type. Must be 'INVOICE' or 'BANKSTMT'.")

    # Set the filename
    filename = "Invoice_allkeys.csv" if document_type == "INVOICE" else "Bankstmt_allkeys.csv"
    SFTP_HOST = os.getenv("SFTP_HOST")
    SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
    SFTP_USERNAME = os.getenv("SFTP_USERNAME")
    SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
    SFTP_UPLOAD_DIR = "/files/ocr_files/"
    # Read file content into memory
    content = await file.read()
    file_obj = BytesIO(content)

    try:
        # Connect to SFTP
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        # Ensure directory exists or create
        try:
            sftp.chdir(SFTP_UPLOAD_DIR)
        except IOError:
            sftp.mkdir(SFTP_UPLOAD_DIR)
            sftp.chdir(SFTP_UPLOAD_DIR)

        # Upload and replace if exists
        sftp.putfo(file_obj, os.path.join(SFTP_UPLOAD_DIR, filename))

        sftp.close()
        transport.close()

        return JSONResponse(content={"status": "success", "message": f"Uploaded as {filename}"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SFTP Upload Failed: {e}")


############################################################
# Main Process 
############################################################

