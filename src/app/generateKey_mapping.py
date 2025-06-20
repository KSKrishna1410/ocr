import csv
import re
from io import StringIO
from src.app.gl_utilities import read_file_from_sftp
from ..config.db.models import fetch_ocr_documents
import asyncio

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
    """Generate key mapping from local CSV files"""
    key_mapping = {}
    all_keys = []

    # Use local CSV files instead of database
    if doctype.lower() == 'invoice':
        csv_path = "Invoice_allkeys.csv"
    elif doctype.lower() == 'bankstmt' or doctype.lower() == 'bank statement':
        csv_path = "bankstmt_allkeys.csv"
    else:
        raise ValueError("Currently only 'Invoice and BANKSTMT' document type is supported.")

    try:
        # Read the local CSV file
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            for row in reader:
                if len(row) >= 2:
                    key, doc_text = row[0].strip(), row[1].strip()

                    if key not in key_mapping:
                        key_mapping[key] = [doc_text]
                        all_keys.append(key)  # Add only the first time
                    else:
                        key_mapping[key].append(doc_text)

        print(f'Loaded field mappings from {csv_path}: {len(key_mapping)} fields')
        return key_mapping

    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_path}")
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    except Exception as e:
        print(f"❌ Error reading CSV file {csv_path}: {e}")
        raise e

class documentClassifier:
    
    def __init__(self):
        # Load keys from CSV files instead of database
        self.invoice_key_mapping = {}
        self.invoice_keywords = []
        self.bank_key_mapping = {}
        self.bank_keywords = []
        self.remittance_key_mapping = {}
        self.remittance_keywords = []
        self.validDocument = ['INVOICE', 'BANKSTMT','REMITTANCE' ]
        self.invoiceMasterInfo = {}
        self.bankMasterInfo = {}
        self.remittanceMasterInfo = {}
        
        # Load from CSV files
        self._load_csv("Invoice_allkeys.csv", self.invoice_key_mapping, self.invoice_keywords, self.invoiceMasterInfo)
        self._load_csv("bankstmt_allkeys.csv", self.bank_key_mapping, self.bank_keywords, self.bankMasterInfo)
        
        self.doc_type_mapping = {
            'INVOICE': self.invoice_key_mapping,
            'BANKSTMT': self.bank_key_mapping,
            'REMITTANCE': self.remittance_key_mapping
        }
        
    @classmethod
    async def create(cls):
        print(f'document processed with type as  {cls}')
        self = cls()
        return self   
    
    def _load_csv(self, csv_path, key_mapping, all_keys, masterInfo):
        all_key_mapping = {}
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                print(f'Loading document type from {csv_path}')
                
                for row in reader:
                    if len(row) >= 4:
                        key, doc_text, dataType, fieldType = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
                        
                        if key != 'Others' and fieldType == 'Header':
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
                            
                        if key not in masterInfo:
                            masterInfo[key] = {
                                "key": key,
                                "dataType": dataType,
                                "fieldType": fieldType,
                                "fieldKeys": ''
                            }
                            
                for key, field_keys_list in all_key_mapping.items():
                    masterInfo[key]['fieldKeys'] = field_keys_list
                    
                print(f'Loaded {len(key_mapping)} fields from {csv_path}')
                
        except FileNotFoundError:
            print(f"❌ CSV file not found: {csv_path}")
        except Exception as e:
            print(f"❌ Error reading CSV file {csv_path}: {e}")
    
    def classify_document(self, text):
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        
        invoice_score = sum(1 for word in self.invoice_keywords if word.lower() in text.lower())
        bank_score = sum(1 for word in self.bank_keywords if word.lower() in text.lower())
        print(f'Document matched Invoice Score ---> {invoice_score} and Bank stmt score {bank_score}')
        if 5 < invoice_score > bank_score:
            # return "INVOICE"
            # Check for invoice, credit note, debit note
            if re.search(r'\bcredit\s+note\b', text.lower()):
                return "CREDIT_NOTE"
            elif re.search(r'\bdebit\s+note\b', text.lower()):
                return "DEBIT_NOTE"
            else :
                return "INVOICE"
        elif 5 < bank_score > invoice_score:
            return "BANKSTMT"
        elif re.search(r'credit\s*card\s*(statement|number|account|txn|transaction)', text.lower()):
            return "CREDIT_CARD_STATEMENT"
        else:
            return "UNKNOWN"

        

# key_mapping = generate_key_mapping_remote('invoice')

# # Print the dictionary
# print("key_mapping =", key_mapping)