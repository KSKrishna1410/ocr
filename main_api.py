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

from tempfile import TemporaryDirectory, SpooledTemporaryFile
from PIL import Image
from fastapi import FastAPI, File, UploadFile,Request, Form # type: ignore
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from uuid import uuid4
from typing import Optional, Literal
from pathlib import Path
from datetime import datetime

from gl_convert_pdftoImage import pdf2ImageMethod
# from gl_getKeyValueResults import process_document
from gl_KeyValueIdentifier import OCRExtractorAndSaver, DocumentAnalyzer
from generateKey_mapping import generate_key_mapping_remote
from gl_mPgTableExtraction import runTabuleProcess_file
from gl_utilities import get_bank_name, extract_first_match, saveBankInfo, cleanTabulaData_remote, upload_to_sftp,prepareRemotePath,convert_ndarray



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


############################################################
# Main Process 
############################################################

def processOcr(folder_path, docType, file, uniqueId):
    print(f"\U0001F4C2 Inside main function:")
    file_name = os.path.splitext(file)[0]
    remote_dir, remote_path = handle_file_upload(folder_path, file, file_name, uniqueId)
    image_paths, fileType = handle_image_conversion(folder_path, file, remote_dir)
    keyMappingData = []
    if not image_paths:
        print("❌ No images found for processing.")
        return

    print(f"✅ Found {len(image_paths)} images. Processing...")
    finalOutput = initialize_output(uniqueId, remote_path, remote_dir, docType, fileType)

    if docType:
        keyMappingData = generate_key_mapping_remote(docType)
    extracted_data, ifsc_code = process_images(image_paths, remote_dir, keyMappingData, finalOutput, docType)

    if docType == 'BANKSTMT' and ifsc_code:
        bank_name = enrich_bank_info(ifsc_code, file_name, remote_dir)
    else:
        bank_name = None

    if file.lower().endswith(".pdf"):
        tableInfo = handle_tabular_data(folder_path, file, remote_dir, docType, bank_name)
        finalOutput["lineTabulaData"] = tableInfo

    upload_results(remote_dir, file_name, finalOutput)
    return finalize_output(finalOutput)

def handle_file_upload(folder_path, file, file_name, uniqueId):
    remote_dir = prepareRemotePath(file_name, uniqueId)
    file_path = os.path.join(folder_path, file)
    with open(file_path, "rb") as f:
        remote_path = upload_to_sftp(f.read(), file, remote_dir)
    print(f"🌐 SFTP Path: {remote_path}")
    return remote_dir, remote_path

def handle_image_conversion(folder_path, file, remote_dir):
    if file.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
        return pdf2ImageMethod(folder_path, remote_dir, folder_path, file)
    print("❌ Unsupported file format.")
    return [], None

def initialize_output(uniqueId, remote_path, remote_dir, docType, fileType):
    return {
        "processId": uniqueId,
        "filePath": remote_path,
        "fileDir": remote_dir,
        "document_type": docType.upper() if docType else None,
        "rawtext": '',
        "fileType": fileType,
        "headerData": [],
        "lineTabulaData": []
    }

def process_images(image_paths, remote_dir, keyMappingData, finalOutput, docType):
    ifsc_code = None
    for index, image_path in enumerate(image_paths):
        print(f"\n🔍 Processing Image: {image_path}")
        page_file_name = os.path.splitext(os.path.basename(image_path))[0]

        ocr_extraction = OCRExtractorAndSaver(image_path, page_file_name, remote_dir)
        if ocr_extraction.perform_ocr_and_save():
            analyzer = DocumentAnalyzer(
                doc_name=page_file_name,
                image_path=image_path,
                result=ocr_extraction.result,
                raw_text=ocr_extraction.raw_text,
                key_mapping_data=keyMappingData,
                sftp_uploader=upload_to_sftp,
                remote_path=remote_dir
            )
            extracted_data = analyzer.analyze_and_extract()
            finalOutput["headerData"].append({
                "page": index + 1,
                "identified_doc_type": analyzer.actual_doc_type,
                "rawtext": ocr_extraction.raw_text,
                "extractedData": extracted_data
            })

            if isinstance(extracted_data, str):
                extracted_data = json.loads(extracted_data)

            if docType == 'BANKSTMT':
                for item in extracted_data:
                    if item.get("key") == "IFSC Code":
                        pattern = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
                        ifsc_code = extract_first_match(item.get("value"), pattern) or ifsc_code
                        print('🏦 IFSC Code fetched:', ifsc_code)
    return extracted_data, ifsc_code

def enrich_bank_info(ifsc_code, file_name, remote_dir):
    print('📘 Fetching bank details for IFSC...')
    bankDetails = get_bank_name(ifsc_code)
    print('🏦 BankInfo:', bankDetails)
    saveBankInfo(bankDetails, file_name, remote_dir)
    return bankDetails.get("BANK")

def handle_tabular_data(folder_path, file, remote_dir, docType, bank_name):
    tableInfo = runTabuleProcess_file(os.path.join(folder_path, file))
    if tableInfo:
        return cleanTabulaData_remote(remote_dir, tableInfo, docType, file, bank_name)
    return []

def upload_results(remote_dir, file_name, finalOutput):
    json_str = json.dumps(finalOutput, indent=4, default=convert_ndarray)
    remote_file_name = f"{file_name}_final.json"
    upload_to_sftp(json_str.encode("utf-8"), remote_file_name, remote_dir)

def finalize_output(finalOutput):
    if not finalOutput.get("lineTabulaData") and finalOutput.get("fileType") != 'Image':
        finalOutput["fileType"] = 'Scanned Document'
    return convert_ndarray(finalOutput)
