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
    all_keys = []
    if doctype.lower() == 'invoice' :
        remote_csv_path = "/files/ocr_files/Invoice_keys.csv"
    elif doctype.lower() == 'bankstmt' or doctype.lower() =='bank statement':
        remote_csv_path = "/files/ocr_files/bankstmt_keys.csv"
    else:
        raise ValueError("Currently only 'Invoice and BANKSTMT' document type is supported.")

    # 🔄 Get CSV content as bytes and decode to string
    csv_bytes = read_file_from_sftp(remote_csv_path)
    csv_string = csv_bytes.decode("utf-8")

    # 🧠 Read CSV in memory
    reader = csv.reader(StringIO(csv_string))
    next(reader)  # Skip header

    for row in reader:
        key, doc_text = row[0].strip(), row[1].strip()

        if key not in key_mapping:
            key_mapping[key] = [doc_text]
            all_keys.append(key)  # Add only the first time
        else:
            key_mapping[key].append(doc_text)

    return key_mapping



class documentClassifier:
    
    def __init__(self):
        # Load keys
        self.invoice_key_mapping = {}
        self.invoice_keywords = []
        self.bank_key_mapping = {}
        self.bank_keywords = []
        self.validDocument = ['INVOICE', 'BANKSTMT' ]
        
        self._load_csv("/files/ocr_files/Invoice_keys.csv", self.invoice_key_mapping, self.invoice_keywords)
        self._load_csv("/files/ocr_files/bankstmt_keys.csv", self.bank_key_mapping, self.bank_keywords)
        self.doc_type_mapping = {
            'INVOICE': self.invoice_key_mapping,
            'BANKSTMT': self.bank_key_mapping
        }
        
        
    def _load_csv(self, remote_csv_path, key_mapping, all_keys):
        csv_bytes = read_file_from_sftp(remote_csv_path)
        csv_string = csv_bytes.decode("utf-8")

        reader = csv.reader(StringIO(csv_string))
        next(reader)  # Skip header

        for row in reader:
            key, doc_text = row[0].strip(), row[1].strip()

            if key not in key_mapping:
                key_mapping[key] = [doc_text]
            else:
                key_mapping[key].append(doc_text)
            
            if doc_text not in all_keys:
                all_keys.append(doc_text)
                
        
    def classify_document(self, text):
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        
        invoice_score = sum(1 for word in self.invoice_keywords if word.lower() in text.lower())
        bank_score = sum(1 for word in self.bank_keywords if word.lower() in text.lower())

        if invoice_score > bank_score:
            return "INVOICE"
        elif bank_score > invoice_score:
            return "BANKSTMT"
        else:
            return "Unknown"

        

# key_mapping = generate_key_mapping_remote('invoice')

# # Print the dictionary
# print("key_mapping =", key_mapping)