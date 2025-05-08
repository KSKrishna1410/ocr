import csv
from io import StringIO
from src.gl_utilities import read_file_from_sftp

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
        self.invoiceMasterInfo = {}
        self.bankMasterInfo = {}
        self._load_csv("/files/ocr_files/Invoice_allkeys.csv", self.invoice_key_mapping, self.invoice_keywords, self.invoiceMasterInfo)
        self._load_csv("/files/ocr_files/bankstmt_allkeys.csv", self.bank_key_mapping, self.bank_keywords, self.bankMasterInfo)
        self.doc_type_mapping = {
            'INVOICE': self.invoice_key_mapping,
            'BANKSTMT': self.bank_key_mapping
        }
        
        
    def _load_csv(self, remote_csv_path, key_mapping, all_keys, masterInfo):
        all_key_mapping= {}
        csv_bytes = read_file_from_sftp(remote_csv_path)
        csv_string = csv_bytes.decode("utf-8")

        reader = csv.reader(StringIO(csv_string))
        next(reader)  # Skip header

        for row in reader:
            key, doc_text,dataType, fieldType = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
            if key != 'Others' and fieldType == 'Header' :
                if key not in key_mapping:
                    key_mapping[key] = [doc_text]
                else:
                    key_mapping[key].append(doc_text)
            
            if key not in all_key_mapping:
                all_key_mapping[key] = [doc_text]
            else:
                all_key_mapping[key].append(doc_text)
            
            if doc_text not in all_keys:
                all_keys.append(doc_text)
            if  key not in masterInfo:
                masterInfo[key] = {
                        "key": key,
                        "dataType": dataType,
                        "fieldType": fieldType,
                        "fieldKeys": ''
                }
        for key, field_keys_list in all_key_mapping.items():
            masterInfo[key]['fieldKeys'] = field_keys_list
        # print(f'Inside KeyValueIdentifierClass {masterInfo}')
                
        
    def classify_document(self, text):
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        
        invoice_score = sum(1 for word in self.invoice_keywords if word.lower() in text.lower())
        bank_score = sum(1 for word in self.bank_keywords if word.lower() in text.lower())
        print(f'Document matched Invoice Score ---> {invoice_score} and Bank stmt score {bank_score}')
        if 5 < invoice_score > bank_score:
            return "INVOICE"
        elif 5 < bank_score > invoice_score:
            return "BANKSTMT"
        else:
            return "UNKNOWN"

        

# key_mapping = generate_key_mapping_remote('invoice')

# # Print the dictionary
# print("key_mapping =", key_mapping)