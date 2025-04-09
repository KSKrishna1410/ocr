import os
import argparse
import shutil
import io
import uuid
import json
import numpy as np
import pandas as pd
import time
import traceback
import sys

from PIL import Image
from fastapi import FastAPI, File, UploadFile, Form # type: ignore
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from uuid import uuid4
from typing import Optional, Literal


from gl_convert_pdftoImage import pdf2ImageMethod
from gl_getKeyValueResults import process_document
from generateKey_mapping import generate_key_mapping_remote
from gl_mPgTableExtraction import runTabuleProcess_file
from gl_utilities import get_bank_name, extract_first_match, saveBankInfo, cleanTabulaData_remote, upload_to_sftp, cleanTabulaData

app = FastAPI()


# Ensure temp directory exists
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/ocr_process/")
async def ocr_process_file(
    file: UploadFile = File(...),
    doctype: Literal["invoice", "bankstmt"] = Form(...)
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

def prepareRemotePath(fileName,uniqueId):
    # REMOTE_DIR = os.getenv("REMOTE_DIR", "/files/inHouseOCR")
    REMOTE_DIR = "/files/inHouseOCR"
    # Get file_name without extension
    file_name = os.path.splitext(fileName)[0]
    print('Inside SFTP connection method file_name', file_name)
    # Get current timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    # Construct remote_dir = REMOTE_DIR/file_name/timestamp
    remote_dir = f"{REMOTE_DIR}/{uniqueId}"
    return remote_dir


def processOcr(folder_path, docType, file,uniqueId):
    print(f"📂 Inside main function:")
    extracted_data = ""
    remote_path = ""
    ifsc_code = None
    bank_name = None
    file_name = os.path.splitext(file)[0]
    
    remote_dir = prepareRemotePath(file_name,uniqueId)
    keyMappingData = generate_key_mapping_remote(docType)

    file_path = os.path.join(folder_path, file)
    print(f"📄 Filename: {file_name}")

    # Upload original file to SFTP
    with open(file_path, "rb") as f:
        file_content = f.read()
        remote_path = upload_to_sftp(file_content, file, remote_dir)
    print(f"🌐 SFTP Path: {remote_path}")

    # Convert PDF/image to images and get image paths
    if file.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
        image_paths = pdf2ImageMethod(folder_path, remote_dir, folder_path, file)
    else:
        print("❌ Unsupported file format.")
        return

    if not image_paths:
        print("❌ No images found for processing.")
        return

    print(f"✅ Found {len(image_paths)} images. Processing...")

    finalOutput = {
        "processId": uniqueId,
        "filePath": remote_path,
        "fileDir": remote_dir,
        "document_type": docType.upper(),
        "headerData": [],
        "lineTabulaData": []
    }

    tableInfo = []
    # Loop through each image
    for index, image_path in enumerate(image_paths):
        print(f"\n🔍 Processing Image: {image_path}")
        page_file_name = os.path.splitext(os.path.basename(image_path))[0]

        # Process the image using your custom OCR pipeline
        extracted_data = process_document(image_path, page_file_name, remote_dir, keyMappingData)

        if isinstance(extracted_data, str):
            extracted_data = json.loads(extracted_data)

        # Special handling for bank statement
        if docType == 'bankstmt':
            for item in extracted_data:
                if item.get("key") == "IFSC Code":
                    ifsc_pattern = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
                    ifsc_code = extract_first_match(item.get("value"), ifsc_pattern) or ifsc_code
                    print('🏦 IFSC Code fetched:', ifsc_code)
            if ifsc_code is None:
                print("⚠️ IFSC Code not found")

        finalOutput["headerData"].append({
            "page": index + 1,
            "extractedData": extracted_data
        })
    # Fetch bank name if IFSC code was found
    if docType == 'bankstmt' and ifsc_code:
        print('📘 Fetching bank details for IFSC...')
        bankDetails = get_bank_name(ifsc_code)
        print('🏦 BankInfo:', bankDetails)
        bank_name = bankDetails.get("BANK")
        saveBankInfo(bankDetails, file_name, remote_dir)

    # Run Tabula if file is PDF
    if file.lower().endswith(".pdf"):
        filepath = os.path.join(folder_path, file)
        tableInfo = runTabuleProcess_file(filepath)

        if tableInfo:
            cleanedData = cleanTabulaData_remote(remote_dir, tableInfo, docType, file, bank_name)
            finalOutput["lineTabulaData"] = cleanedData
        # finalOutput["lineTabulaData"] = tableInfo
    print('✅ Completed Table Extraction:', tableInfo)

    # finalJsonoutput_path = os.path.join(output_folder, f"{file_name}_final.json")
    # with open(finalJsonoutput_path, "w", encoding="utf-8") as json_file:
    #     json.dump(finalOutput, json_file, indent=4)
    # Convert your finalOutput into JSON string
    json_str = json.dumps(finalOutput, indent=4, default=convert_ndarray)
    json_bytes = json_str.encode("utf-8") # Encode to bytes
    remote_file_name = f"{file_name}_final.json" # Define the remote file name and directory

    # Upload to SFTP using your common method
    upload_to_sftp(json_bytes, remote_file_name, remote_dir)
    print("✅ Type of finalOutput:", type(finalOutput))
    print("📦 Type of headerData:", type(finalOutput.get("headerData")))
    print("📦 Type of lineTabulaData:", type(finalOutput.get("lineTabulaData")))

    for idx, item in enumerate(finalOutput.get("lineTabulaData", [])):
        print(f"🔍 lineTabulaData[{idx}] type:", type(item))
    final_output = convert_ndarray(finalOutput)
    return final_output



def main(input_folder, output_folder, docType):
    print(f"Inside main function:")
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    extracted_data = ""
    # Convert PDFs to images and get list of image paths
    keyMappingData = generate_key_mapping(docType);
    for index, file in enumerate(os.listdir(input_folder)):
        file_path = os.path.join(input_folder, file)
        
        if os.path.isfile(file_path):
            file_name = os.path.splitext(file)[0]  # Extract filename without extension
            
            ifsc_code = None
            bank_name = None
            print(f"Filename: {file_name}")  # Print or store it for further use
            with open(file_path, "rb") as f:
                file_content = f.read()
                remote_path = upload_to_sftp(file_content, file_name,'')
            print(f"SFTP Path: {remote_path}")
            if file.lower().endswith((".jpg", ".jpeg", ".png",".pdf")):
                image_paths = pdf2ImageMethod(input_folder, output_folder,file)
            else:
                continue
            image_paths = pdf2ImageMethod(input_folder, output_folder,file)
        
            if not image_paths:
                print("❌ No images found for processing.")
                return

            print(f"✅ Found {len(image_paths)} images. Processing...")
            finalOutput = {
                "headerData": [],
                "lineTabulaData": []
            }
            tableInfo = []
            # Loop through each image path and process the invoice
            for index, image_path in enumerate(image_paths):
                print(f"\n🔍 Processing Image: {image_path}")
                page_file_name = os.path.splitext(os.path.basename(image_path))[0]
                # layoutOutput = detectImage(image_path,page_file_name,output_folder)
                
                extracted_data = process_document(image_path,page_file_name,output_folder,keyMappingData)
                base_name = os.path.splitext(os.path.basename(image_path))[0]  # Extract filename without extension
                output_path = os.path.join(output_folder, f"{base_name}.json")  # Save JSON in output folder

                # Save JSON file
                # with open(output_path, "w", encoding="utf-8") as json_file:
                #     json_file.write(extracted_data)
                # Convert extractedData from string to list
                if isinstance(extracted_data, str):
                    extracted_data = json.loads(extracted_data)
                if (docType == 'bankstmt'):
                    for item in extracted_data:
                        if item.get("key") == "IFSC Code":
                            ifsc_pattern = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
                            ifsc_code = extract_first_match(item.get("value"), ifsc_pattern) or ifsc_code
                            print('IFSC Code fetched is --------->  ', ifsc_code)
                    print("IFSC_Code not found")
                finalOutput["headerData"].append({
                    "page": index+1,
                    "extractedData": extracted_data
                })
                # print(f"✅ finalOutput after page:{index+1} and data is {finalOutput}")
                print(f"✅ JSON output saved: {output_path}")
                # break 
            if (docType == 'bankstmt' and ifsc_code != None):
                print('Inside  Bankstmt fetch details----->')
                bankDetails = get_bank_name(ifsc_code)
                print('BankInfo  ----->', bankDetails)
                bank_name = bankDetails.get("BANK")
                saveBankInfo(bankDetails,file_name, output_folder)
            if file.lower().endswith(".pdf"):
                filepath = os.path.join(input_folder, file)
                tableInfo = runTabuleProcess_file(filepath)
                if len(tableInfo) > 0:  
                    cleanedData = cleanTabulaData(output_folder,tableInfo,docType,file,bank_name)
                    finalOutput["lineTabulaData"] = cleanedData
            print('Complete Extracted code -------> ', tableInfo)
            finalJsonoutput_path = os.path.join(output_folder, f"{file_name}_final.json")
            # with open(finalJsonoutput_path, "w", encoding="utf-8") as json_file:
            #         json_file.write(finalOutput)
            # with open(finalJsonoutput_path, "w") as json_file:
            #     json.dump(finalOutput, json_file, indent=4, default=convert_ndarray)
    return extracted_data

# def convert_ndarray(obj):
#     if isinstance(obj, np.ndarray):
#         return obj.tolist()  # Convert ndarray to list
#     raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def convert_ndarray(obj):
    if isinstance(obj, dict):
        return {k: convert_ndarray(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ndarray(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_ndarray(item) for item in obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')  # or use 'split', 'index' as needed
    else:
        return obj
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract invoice details from PDFs in a folder.")
    parser.add_argument("input_folder", type=str, help="Path to the input folder containing PDFs")
    parser.add_argument("output_folder", type=str, help="Path to the output folder for extracted images")
    parser.add_argument("docType", type=str, help="Document type not Specified")

    args = parser.parse_args()
    
    main(args.input_folder, args.output_folder, args.docType)

# python main.py "/workspace/nishanth/newprj/paddleOCRKey/docs/" "/workspace/nishanth/newprj/paddleOCRKey/docs/processDocs" invoice
# python .\main.py "C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\docs" "C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\docs\images"