import os
import json
from uuid import uuid4

from src.gl_convert_pdftoImage import pdf2ImageMethod
from src.gl_KeyValueIdentifier import OCRExtractorAndSaver, DocumentAnalyzer
from src.generateKey_mapping import generate_key_mapping_remote
from src.gl_mPgTableExtraction import runTabuleProcess_file
from src.gl_utilities import get_bank_name, extract_first_match, saveBankInfo, cleanTabulaData_remote, upload_to_sftp,prepareRemotePath,convert_ndarray

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
        # if len(tableInfo) > 2:
        #     finalOutput["pageWiseData"][0]['lineInfo']['lineData'] = tableInfo

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
        "pageWiseData": [],
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
            finalOutput["pageWiseData"].append({
                "page": index + 1,
                "identified_doc_type": analyzer.actual_doc_type,
                "rawtext": ocr_extraction.raw_text,
                "headerInfo": extracted_data,
                "lineInfo": analyzer.ppOCRTableData
            })
            # ppOCRTableData['lineData']
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