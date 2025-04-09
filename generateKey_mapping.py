import csv
from io import StringIO
from gl_utilities import read_file_from_sftp

def generate_key_mapping(doctype):
    key_mapping = {}
    # Usage
    if doctype.lower() == 'invoice':
        csv_file_path = "inputs/Invoice_keys.csv"  # file path
    elif doctype.lower() == 'bankstmt':
        csv_file_path = "inputs/bankstmt_keys.csv"  # file path
    # Read the CSV file
    with open(csv_file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            key, doc_text = row[0].strip(), row[1].strip()

            # Append doc_text to the corresponding key in key_mapping
            if key in key_mapping:
                key_mapping[key].append(doc_text)
            else:
                key_mapping[key] = [doc_text]

    return key_mapping

def generate_key_mapping_remote(doctype):
    key_mapping = {}

    if doctype.lower() == 'invoice':
        remote_csv_path = "/files/ocr_files/Invoice_keys.csv"
    elif doctype.lower() == 'bankstmt':
        remote_csv_path = "/files/ocr_files/bankstmt_keys.csv"
    else:
        raise ValueError("Currently only 'invoice and Bankstmt' document type is supported.")

    # 🔄 Get CSV content as bytes and decode to string
    csv_bytes = read_file_from_sftp(remote_csv_path)
    csv_string = csv_bytes.decode("utf-8")

    # 🧠 Read CSV in memory
    reader = csv.reader(StringIO(csv_string))
    next(reader)  # Skip header

    for row in reader:
        key, doc_text = row[0].strip(), row[1].strip()

        if key in key_mapping:
            key_mapping[key].append(doc_text)
        else:
            key_mapping[key] = [doc_text]

    return key_mapping

# key_mapping = generate_key_mapping_remote('invoice')

# # Print the dictionary
# print("key_mapping =", key_mapping)