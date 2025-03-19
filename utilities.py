import requests
import re
import os
import csv
import numpy as np

csv_file = "key_pair_extracted_data.csv"
bank_headers = {
    "ICICI Bank": ["SrNo", "TranID", "ValueDate", "TransactionDate", "Chequeno/RefNo",
                    "TransactionRemarks", "Withdrawl(Dr)", "Deposit(Cr)", "Balance"],
    "AXIS": ["Txn Date", "Transaction", "Withdrawals", "Deposits", "Balance", "Other Information"],
    "IDFC": ["TransactionDate", "Value Date", "Particulars", "ChequeNo", "Debit", "Credit", "Balance"],
    "State Bank of India": ["Post Date", "Value Date", "Description", "ChequeNo/Reference", "Debit", "Credit", "Balance"]
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
    print('Inside CSV printing ----->   ', extracted_data)
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
                writer.writerow(["File Name", "Key", "Value", "key_bbox", "value_bbox","method", "doc_text" ])  # CSV Headers
            # Append extracted data
            for obj in extracted_data:
                # writer.writerow([file_name, obj["key"], obj["value"], obj["key_bbox"], obj["value_bbox"],obj["method"], obj["doc_text"]])
                writer.writerow([
                    file_name,
                    obj.get("key", ""),
                    obj.get("value", ""),
                    obj.get("key_bbox", ""),
                    obj.get("value_bbox", ""),
                    obj.get("method", ""),
                    obj.get("doc_text", "")
                ])
        print(f"✅ Data appended to CSV: {csv_path}")

    except Exception as e:
        print(f"❌ Error saving extracted data to CSV: {e}")
        
def saveBankInfo(bankDetails,file_name,opfldr):
    # Filtering non-empty and non-None values
    filtered_data = [{ "file_name": file_name, "key": k, "value": v, "method":"master_info" } for k, v in bankDetails.items() if v not in [None, ""]]
    # Output
    print("Bank Dictoniary data ->", filtered_data)
    # bankMasterInfo = json.dumps(filtered_data, indent=4)  
    save_extracted_data(filtered_data, opfldr, file_name)
    return 

def is_header_row(row,expected_headers):
    return sum(1 for keyword in expected_headers if any(keyword.lower() in str(cell).lower() for cell in row)) >= len(expected_headers) - 2


def cleanTabulaData(folderpath,final_array,docType, document, bank_name):
    csv_output_path = folderpath+document+'TabulaData.csv'
    data = []
    expected_headers = bank_headers.get(bank_name, [])  # Return empty list if bank not found
    print(f'Expected header -- {len(expected_headers)}  final_array[0] length --> {len(final_array[0])} and the final array is {final_array[0]}')
    if (docType == 'bankstmt' and len(expected_headers) > 0):
        expected_length = len(expected_headers)  # Reference length
        # Find the header row index
        header_index = next((i for i, row in enumerate(final_array) if is_header_row(row, expected_headers)), None)
        print(f'Header data and it index found at ----------------> {header_index}')
        if header_index is not None:
            final_array = final_array[header_index:]  # Keep from the header row onwards
        else: print("❌ Error: Header row not found!")
    else: 
        expected_length = len(final_array[0])
    # Convert existing data to a set for fast lookup
    existing_rows = set(tuple(row) for row in data)  # Convert list to a set of tuples
    with open(csv_output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for eachrow in final_array:
            eachrow = [" " if (isinstance(x, float) and np.isnan(x)) or x == "nan" else x for x in eachrow]
            row_tuple = tuple(eachrow)  # Convert list to tuple for easy comparison
            row_length = len(eachrow)  # Get row length
            print(f'expected_length but got {expected_length} and  rowlenght {row_length}')
            if row_tuple not in existing_rows and (expected_length - 1 <= row_length <= expected_length + 1):  # Check for duplicate and row lenght
                writer.writerow(eachrow)  # Write to CSV
                data.append(eachrow)  # Add to data list
                existing_rows.add(row_tuple)  # Mark row as added
            else:
                print("🚨 Duplicate row skipped:", eachrow)

    return data