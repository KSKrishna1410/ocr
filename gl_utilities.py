import requests
import re
import os
import csv
import numpy as np
import pandas as pd
import os
import paramiko
from dotenv import load_dotenv
import time
import io

load_dotenv()

csv_file = "key_pair_extracted_data.csv"
bank_headers = {
    "ICICI Bank": [["SrNo", "TranID", "ValueDate", "TransactionDate", "Chequeno/RefNo",
                    "TransactionRemarks", "Withdrawl(Dr)", "Deposit(Cr)", "Balance"],['DATE', 'MODE**', 'PARTICULARS', 'DEPOSITS', 'WITHDRAWALS', 'BALANCE']],
    "Axis Bank": [["Txn Date", "Transaction", "Withdrawals", "Deposits", "Balance", "Other Information"],["Tran Date", "Chq No", "Particulars", "Debit", "Credit", "Balance", "Init.Br"]],
    "IDFC": [["TransactionDate", "Value Date", "Particulars", "ChequeNo", "Debit", "Credit", "Balance"]],
    "State Bank of India": [["Post Date", "Value Date", "Description", "ChequeNo/Reference", "Debit", "Credit", "Balance"]]
}

# def getBankHeaders(bank_name):
#     if bank_name == 'ICICI Bank':
#         expected_headers = [SrNo	TranID	ValueDate	TransactionDate	Chequeno/  RefNo	TransactionRemarks	Withdrawl(Dr)	Deposit(Cr)	Balance]
#     if bank_name == 'AXIS':
#         expected_headers = ["Txn Date", "Transaction", "Withdrawals", "Deposits", "Balance", "Other Information"]
#     if bank_name == 'IDFC':
#         expected_headers = [TransactionDate	Value Date	Particulars	ChequeNo	Debit	Credit	Balance]
#     if bank_name == 'SBI':
#         expected_headers = [Post Date	Value Date	Description	ChequeNo/Reference	Debit	Credit	Balance]
    

def get_bank_name(ifsc_code):
    url = f"https://ifsc.razorpay.com/{ifsc_code}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # print('Bank detaiks', data)
        return data
        # return data.get("BANK", "Bank name not found")
    else:
        return "Invalid IFSC code"


def extract_first_match(text, pattern):
    # pattern = r"[A-Z]{4}0\d{6}"  # Your regex pattern
    match = re.search(pattern, text)  # Search for the first match
    return match.group(0) if match else None  # Return match or None

def save_extracted_data(extracted_data, output_folder, file_name):
    """Saves extracted key-value pairs to a text file."""
    # print('Inside CSV printing ----->   ', extracted_data)
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    csv_path = os.path.join(output_folder, csv_file)
    # Check if the CSV file exists to determine if headers are needed
    file_exists = os.path.isfile(csv_path)

    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write headers only if the file is being created for the first time
            if not file_exists:
                writer.writerow(["File Name", "Key", "Value","method", "key_bbox", "value_bbox", "doc_text" ])  # CSV Headers
            # Append extracted data
            for obj in extracted_data:
                # writer.writerow([file_name, obj["key"], obj["value"], obj["key_bbox"], obj["value_bbox"],obj["method"], obj["doc_text"]])
                writer.writerow([
                    file_name,
                    obj.get("key", ""),
                    obj.get("value", ""),
                    obj.get("method", ""),
                    obj.get("key_bbox", ""),
                    obj.get("value_bbox", ""),
                    obj.get("doc_text", "")
                ])
        print(f"✅ Data appended to CSV: {csv_path}")

    except Exception as e:
        print(f"❌ Error saving extracted data to CSV: {e}")


def save_extracted_data_remote(extracted_data, remote_dir, file_name):
    """Saves extracted key-value pairs to a CSV and uploads to SFTP."""
    
    csv_file = f"{file_name}_extracted_data.csv"
    output_stream = io.StringIO()
    writer = csv.writer(output_stream)

    # Write headers
    writer.writerow(["File Name", "Key", "Value", "method", "key_bbox", "value_bbox", "doc_text"])

    # Write rows
    for obj in extracted_data:
        writer.writerow([
            file_name,
            obj.get("key", ""),
            obj.get("value", ""),
            obj.get("method", ""),
            obj.get("key_bbox", ""),
            obj.get("value_bbox", ""),
            obj.get("doc_text", "")
        ])

    # Upload to SFTP as bytes
    csv_bytes = output_stream.getvalue().encode("utf-8")
    upload_to_sftp(csv_bytes, csv_file, remote_dir)
    print(f"✅ CSV uploaded to SFTP: {csv_file}")
        
def saveBankInfo(bankDetails,file_name,opfldr):
    # Filtering non-empty and non-None values
    filtered_data = [{ "file_name": file_name, "key": k, "value": v, "method":"master_info" } for k, v in bankDetails.items() if v not in [None, ""]]
    # Output
    print("Bank Dictoniary data ->", filtered_data)
    # bankMasterInfo = json.dumps(filtered_data, indent=4)  
    save_extracted_data_remote(filtered_data, opfldr, file_name)
    return 

def normalize(text):
    """Convert text to lowercase and remove all spaces (before, after, and in between)."""
    if isinstance(text, np.ndarray):
        text = text.astype(str)  # Convert NumPy array elements to string
        text = " ".join(text)  # Join elements if it's an array

    return re.sub(r"\s+", "", str(text).strip().lower())

# def is_header_row(row,expected_headers):
#     return sum(1 for keyword in expected_headers if any(keyword.lower() in str(cell).lower() for cell in row)) >= len(expected_headers) - 2


def is_header_row(row, expected_headers):
    # Normalize expected headers
    row = [normalize(row_items) for row_items in row]
    expected_headers = [normalize(header_item) for header_item in expected_headers]
    # Normalize row values before matching
    return sum(
        1 for keyword in expected_headers 
        if any(keyword in normalize(str(cell)) for cell in row)
    ) >= len(expected_headers) - 2

def cleanTabulaData(folderpath,final_array,docType, document, bank_name):
    folderpath += "\\"
    csv_output_path = folderpath+document+'TabulaData.csv'
    data = []
    expected_headers = bank_headers.get(bank_name, [])  # Return empty list if bank not found
    print(f'Expected header -- {len(expected_headers)}  final_array[0] length --> {len(final_array[0])} and the final array is {final_array[0]}')
    if (docType == 'BANKSTMT' and len(expected_headers) > 0):
        matched_header_index = 0
        header_index = None
        # Find the header row index
        # header_index = next((i for i, row in enumerate(final_array) if is_header_row(row, expected_headers)), None)
        for i, row in enumerate(final_array):
            for j, headers in enumerate(expected_headers):
                print(f'Row Item -- {row}  Header fetch --> {headers}')
                if is_header_row(row, headers):
                    header_index = i  # Found header row index in final_array
                    matched_header_index = j  # Found which expected_headers variation matched
                    break  # Stop checking once a match is found
            if header_index is not None:
                break  # Stop the outer loop as well
        
        print(f'Header data and it index found at ----------------> {header_index} Matched expected_headers Index: {matched_header_index}')
        expected_length = len(expected_headers[matched_header_index])  # Reference length
        print(f"Matched expected_headers[matched_header_index]: {expected_headers[matched_header_index]}")
        if header_index is not None:
            final_array = final_array[header_index:]  # Keep from the header row onwards
        else: print("❌ Error: Header row not found!")
    else: 
        expected_length = len(final_array[0])
    # Convert existing data to a set for fast lookup
    existing_rows = set(tuple(row) for row in data)  # Convert list to a set of tuples
    with open(csv_output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        print('Document getting saved at ',csv_output_path)
        for eachrow in final_array:
            # eachrow = [" " if (isinstance(x, float) and np.isnan(x)) or x == "nan" else x for x in eachrow]
            eachrow = [
                " " if (isinstance(x, float) and np.isnan(x)) or str(x).lower() == "nan" else x
                for x in np.array(eachrow).flatten()  # Ensure eachrow is a list of values
            ]
            row_tuple = tuple(eachrow)  # Convert list to tuple for easy comparison
            row_length = len(eachrow)  # Get row length
            print(f'expected_length but got {expected_length} and  rowlenght {row_length}')
            if row_tuple not in existing_rows :  # Check for duplicate and row lenght
            # if row_tuple not in existing_rows and (expected_length - 1 <= row_length <= expected_length + 1):  # Check for duplicate and row lenght
                writer.writerow(eachrow)  # Write to CSV
                data.append(eachrow)  # Add to data list
                existing_rows.add(row_tuple)  # Mark row as added
            else:
                print("🚨 Duplicate row skipped:", eachrow)
    return data

import io
import csv

def cleanTabulaData_remote(remote_dir, final_array, docType, document, bank_name):
    csv_file_name = document + 'TabulaData.csv'
    data = []
    expected_headers = bank_headers.get(bank_name, [])  # Return empty list if bank not found

    print(f'Expected header -- {len(expected_headers)}  final_array[0] length --> {len(final_array[0])} and the final array is {final_array[0]}')

    if docType == 'BANKSTMT' and len(expected_headers) > 0:
        matched_header_index = 0
        header_index = None
        for i, row in enumerate(final_array):
            for j, headers in enumerate(expected_headers):
                print(f'Row Item -- {row}  Header fetch --> {headers}')
                if is_header_row(row, headers):
                    header_index = i
                    matched_header_index = j
                    break
            if header_index is not None:
                break
        
        print(f'Header data and its index found at ----------------> {header_index} Matched expected_headers Index: {matched_header_index}')
        expected_length = len(expected_headers[matched_header_index])
        print(f"Matched expected_headers[matched_header_index]: {expected_headers[matched_header_index]}")
        if header_index is not None:
            final_array = final_array[header_index:]
        else:
            print("❌ Error: Header row not found!")
    else:
        expected_length = len(final_array[0])

    existing_rows = set(tuple(row) for row in data)

    # Write to in-memory string buffer
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)

    for eachrow in final_array:
        eachrow = [
            " " if (isinstance(x, float) and np.isnan(x)) or str(x).lower() == "nan" else x
            for x in np.array(eachrow).flatten()
        ]
        row_tuple = tuple(eachrow)
        row_length = len(eachrow)

        print(f'expected_length but got {expected_length} and  row length {row_length}')
        if row_tuple not in existing_rows:
            writer.writerow(eachrow)
            data.append(eachrow)
            existing_rows.add(row_tuple)
        else:
            print("🚨 Duplicate row skipped:", eachrow)

    print(f"Uploading CSV to remote SFTP: {csv_file_name} -> {remote_dir}")

    # Get byte content from string buffer
    csv_content_bytes = csv_buffer.getvalue().encode("utf-8")
    upload_to_sftp(csv_content_bytes, csv_file_name, remote_dir)

    return data


def prepareRemotePath(fileName,uniqueId):
    # REMOTE_DIR = os.getenv("REMOTE_DIR", "/files/inHouseOCR")
    REMOTE_DIR = "/files/inHouseOCR"
    # Get file_name without extension
    file_name = os.path.splitext(fileName)[0]
    print('Inside SFTP connection method file_name', file_name)
    # Get current timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    # Construct remote_dir = REMOTE_DIR/file_name/timestamp
    # remote_dir = f"{REMOTE_DIR}/{fileName}" #for filename as a folder
    remote_dir = f"{REMOTE_DIR}/{uniqueId}"
    return remote_dir

def ensure_remote_dir_exists(sftp, remote_dir):
    """
    Recursively create directories on the SFTP server if they don't exist.
    """
    dirs = remote_dir.strip("/").split("/")
    current_path = ""
    for directory in dirs:
        current_path += f"/{directory}"
        try:
            sftp.stat(current_path)
        except FileNotFoundError:
            sftp.mkdir(current_path)

def upload_to_sftp(file_content: bytes, filename: str, remote_dir) -> str:
    SFTP_HOST = os.getenv("SFTP_HOST")
    SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
    SFTP_USERNAME = os.getenv("SFTP_USERNAME")
    SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")

    remote_path = f"{remote_dir}/{filename}"

    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            ensure_remote_dir_exists(sftp, remote_dir)
        except Exception as e:
            raise RuntimeError(f"Failed to create remote directory '{remote_dir}': {e}")

        # Upload the file
        try:
            with sftp.file(remote_path, 'wb') as remote_file:
                remote_file.write(file_content)
        except Exception as e:
            raise RuntimeError(f"Failed to upload file to '{remote_path}': {e}")

        sftp.close()
        transport.close()

        return remote_path
    except Exception as e:
        raise RuntimeError(f"SFTP Upload Failed: {e}")
    
def download_from_sftp(remote_filepath: str, local_filepath: str) -> None:
    SFTP_HOST = os.getenv("SFTP_HOST")
    SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
    SFTP_USERNAME = os.getenv("SFTP_USERNAME")
    SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")

    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            sftp.get(remote_filepath, local_filepath)
        except Exception as e:
            raise RuntimeError(f"Failed to download file from '{remote_filepath}': {e}")

        sftp.close()
        transport.close()

    except Exception as e:
        raise RuntimeError(f"SFTP Download Failed: {e}")
    
def read_file_from_sftp(remote_filepath: str) -> bytes:
    SFTP_HOST = os.getenv("SFTP_HOST")
    SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
    SFTP_USERNAME = os.getenv("SFTP_USERNAME")
    SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")

    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            with sftp.file(remote_filepath, "rb") as remote_file:
                content = remote_file.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file from '{remote_filepath}': {e}")
        finally:
            sftp.close()
            transport.close()

        return content

    except Exception as e:
        raise RuntimeError(f"SFTP Read Failed: {e}")

def read_file_from_sftpFldr(remote_path: str) -> bytes:
    SFTP_HOST = os.getenv("SFTP_HOST")
    SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
    SFTP_USERNAME = os.getenv("SFTP_USERNAME")
    SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # List files in remote directory
        remote_files = sftp.listdir(remote_path)
        return remote_files
    except Exception as e:
        return {"error": str(e)}
    
    
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