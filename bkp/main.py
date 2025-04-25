import os
import argparse
from convert_pdftoImage import pdf2ImageMethod
from getKeyValueResults import process_document
from src.generateKey_mapping import generate_key_mapping
from mPgTableExtraction import runTabuleProcess_file
import json
import numpy as np
from utilities import get_bank_name, extract_first_match, saveBankInfo, cleanTabulaData

# from identifyTableData import detectImage

# File Path
# input_folder = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\docs"  # Folder containing PDFs
# output_folder = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\docs\images"  # Folder to save PNGs

def main(input_folder, output_folder, docType):
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    extracted_data = ""
    # Convert PDFs to images and get list of image paths
    keyMappingData = generate_key_mapping(docType);
    for index, file in enumerate(os.listdir(input_folder)):
        file_name = os.path.splitext(file)[0]  # Extract filename without extension
        ifsc_code = None
        bank_name = None
        print(f"Filename: {file_name}")  # Print or store it for further use
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
            with open(output_path, "w", encoding="utf-8") as json_file:
                json_file.write(extracted_data)
            # Convert extractedData from string to list
            if isinstance(extracted_data, str):
                extracted_data = json.loads(extracted_data)
            if (docType == 'BANKSTMT'):
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
        if (docType == 'BANKSTMT' and ifsc_code != None):
            print('Inside  BANKSTMT fetch details----->')
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
        with open(finalJsonoutput_path, "w") as json_file:
            json.dump(finalOutput, json_file, indent=4, default=convert_ndarray)
    return extracted_data

def convert_ndarray(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert ndarray to list
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def processOcr(folder_path, docType, file,uniqueId):
    print(f"📂 Inside main function:")
    extracted_data = ""
    remote_path = ""
    ifsc_code = None
    bank_name = None
    file_name = os.path.splitext(file)[0]
    keyMappingData = []
    remote_dir = prepareRemotePath(file_name,uniqueId)
    if docType:
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
        image_paths, fileType = pdf2ImageMethod(folder_path, remote_dir, folder_path, file)
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
        "document_type": docType.upper() if docType else None,
        "pageSize": len(image_paths),
        "fileType": fileType,
        "headerData": [],
        "lineTabulaData": []
    }

    tableInfo = []
    # Loop through each image
    for index, image_path in enumerate(image_paths):
        print(f"\n🔍 Processing Image: {image_path}")
        page_file_name = os.path.splitext(os.path.basename(image_path))[0]

        # Process the image using your custom OCR pipeline
        # extracted_data = process_document(image_path, page_file_name, remote_dir, keyMappingData)

        ocr_extraction = OCRExtractorAndSaver(
            image_path=image_path,
            doc_name=page_file_name,
            output_folder=remote_dir,
        )

        if ocr_extraction.perform_ocr_and_save():
            analyzer = DocumentAnalyzer(
                doc_name=page_file_name,
                image_path=image_path,
                result=ocr_extraction.result,
                raw_text=ocr_extraction.raw_text,
                key_mapping_data=keyMappingData,
                sftp_uploader=upload_to_sftp,
                remote_path= remote_dir
            )
            extracted_data = analyzer.analyze_and_extract()
            print('Inside main method ----------->', analyzer.actual_doc_type )
            
            finalOutput["headerData"].append({
                "page": index + 1,
                "identified_doc_type": analyzer.actual_doc_type,
                "rawtext" : ocr_extraction.raw_text,
                "extractedData": extracted_data
            })

        if isinstance(extracted_data, str):
            extracted_data = json.loads(extracted_data)

        # Special handling for bank statement
        if docType == 'BANKSTMT':
            for item in extracted_data:
                if item.get("key") == "IFSC Code":
                    ifsc_pattern = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
                    ifsc_code = extract_first_match(item.get("value"), ifsc_pattern) or ifsc_code
                    print('🏦 IFSC Code fetched:', ifsc_code)
            if ifsc_code is None:
                print("⚠️ IFSC Code not found")

        
    # Fetch bank name if IFSC code was found
    if docType == 'BANKSTMT' and ifsc_code:
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

    # Upload to SFTP using your common method
    json_str = json.dumps(finalOutput, indent=4, default=convert_ndarray)
    json_bytes = json_str.encode("utf-8") # Encode to bytes
    remote_file_name = f"{file_name}_final.json" # Define the remote file name and directory
    upload_to_sftp(json_bytes, remote_file_name, remote_dir)

    for idx, item in enumerate(finalOutput.get("lineTabulaData", [])):
        print(f"🔍 lineTabulaData[{idx}] type:", type(item))
    if len(finalOutput.get("lineTabulaData", [])) == 0 and finalOutput.get("fileType") != 'Image':
        finalOutput["fileType"] = 'Scanned Document'
    final_output = convert_ndarray(finalOutput)
    return final_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract invoice details from PDFs in a folder.")
    parser.add_argument("input_folder", type=str, help="Path to the input folder containing PDFs")
    parser.add_argument("output_folder", type=str, help="Path to the output folder for extracted images")
    parser.add_argument("docType", type=str, help="Document type not Specified")

    args = parser.parse_args()
    
    main(args.input_folder, args.output_folder, args.docType)

# python main.py "/workspace/nishanth/newprj/paddleOCRKey/docs/" "/workspace/nishanth/newprj/paddleOCRKey/docs/processDocs" invoice
# python .\main.py "C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\docs" "C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\docs\images"