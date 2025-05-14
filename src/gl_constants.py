regex_check = [
  {
    "key": "SGST Tax Rate",
    "pattern": "(?i)(?=.*SGST).*?(\d{1,2}(?:\.\d{1,2})?)\s*%"
  },
  {
    "key": "CGST Tax Rate",
    "pattern": "(?i)(?=.*CGST).*?(\d{1,2}(?:\.\d{1,2})?)\s*%"
  },
  {
    "key": "IGST Tax Rate",
    "pattern": "(?i)(?=.*IGST).*?(\d{1,2}(?:\.\d{1,2})?)\s*%"
  },
  {
    "key": "GST Tax Rate",
    "pattern": "(?i)\bGST.*?(\d{1,2})\s*%"
  },
  {
    "key": "GSTIN",
    "pattern": "\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}"
  },
  {
    "key": "HSN",
    "pattern": "(?i)(?:sac|hsn)\s*code[:\-]?\s*(\d{4,8})"
  },
  {
    "key": "Amount_in_words",
    "pattern": r'(?:INR|Rupees)?\s*((?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|'
    r'Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|'
    r'Twenty|Thirty|Forty|Fifty|Sixty|Seventy|Eighty|Ninety|'
    r'Hundred|Thousand|Lakh|Crore|Rupees|Paisa|And|Zero)\s+(?:(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|'
    r'Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|'
    r'Twenty|Thirty|Forty|Fifty|Sixty|Seventy|Eighty|Ninety|'
    r'Hundred|Thousand|Lakh|Crore|Rupees|Paisa|And|Zero)\s+)*'
    r'(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|'
    r'Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|'
    r'Twenty|Thirty|Forty|Fifty|Sixty|Seventy|Eighty|Ninety|Rupees|Paisa|Zero))'
    r'\s+(Only|rounding|grand|total|$)'
  }
]

bank_headers = {
    "ICICI Bank": [["SrNo", "TranID", "ValueDate", "TransactionDate", "Chequeno/RefNo",
                    "TransactionRemarks", "Withdrawl(Dr)", "Deposit(Cr)", "Balance"],['DATE', 'MODE**', 'PARTICULARS', 'DEPOSITS', 'WITHDRAWALS', 'BALANCE']],
    "Axis Bank": [["Txn Date", "Transaction", "Withdrawals", "Deposits", "Balance", "Other Information"],["Tran Date", "Chq No", "Particulars", "Debit", "Credit", "Balance", "Init.Br"]],
    "IDFC": [["TransactionDate", "Value Date", "Particulars", "ChequeNo", "Debit", "Credit", "Balance"]],
    "State Bank of India": [["Post Date", "Value Date", "Description", "ChequeNo/Reference", "Debit", "Credit", "Balance"]]
}

feilds_pattern = {
  "CGST Tax Amount": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$",
  "CGST Tax Rate": "^(0\\.25|0\\.5|1|1\\.5|2\\.5|3|5|6|7\\.5|8|9|10|12|14|18|24|28)%$",
  "CIN Number": "^.*$",
  "Customer Name": "^.*$",
  "Discount": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$",
  "Due Date": "\\b(?:(?:\\d{1,2}[-\\/\\.\\s]?)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[-\\/\\.\\s]?\\d{2,4}|\\d{1,2}[-\\/\\.\\s]\\d{1,2}[-\\/\\.\\s]\\d{2,4}|\\d{4}[-\\/\\.\\s]\\d{1,2}[-\\/\\.\\s]\\d{1,2})(?:\\s\\d{2}[:]\\d{2}[:]\\d{2})?\\b",
  "Freight": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$",
  "GSTIN": "\\d{2}[A-Z]{5}\\d{4}[A-Z]{1}[A-Z\\d]{1}[Z]{1}[A-Z\\d]{1}",
  "HSN": "^\\d{4}(\\d{2}){0,1}(\\d{2}){0,1}$",
  "IGST Tax Amount": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$",
  "IGST Tax Rate": "^(0\\.25|0\\.5|1|1\\.5|2\\.5|3|5|6|7\\.5|8|9|10|12|14|18|24|28)%$",
  "Invoice Date New": "\b(?:(?:\d{1,2}[-\/.\s])?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[-\/.\s]?\d{2,4}|\d{1,2}[-\/.\s]\d{1,2}[-\/.\s]\d{2,4}|\d{4}[-\/.\s]\d{1,2}[-\/.\s]\d{1,2}|\d{8})(?:[\sT]\d{2}:\d{2}(?::\d{2})?)?\b",
  "Invoice Number": "^.*$",
  "Invoice Total Amount": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$",
  "IRN No": "^.*$",
  "Net Amount": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$",
  "PAN Number": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
  "PO No#": "^.*$",
  "SGST Tax Amount": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$",
  "SGST Tax Rate": "^(0\\.25|0\\.5|1|1\\.5|2\\.5|3|5|6|7\\.5|8|9|10|12|14|18|24|28)%$",
  "Sub Total Of GST": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$",
  "Supplier Details": "^.*$",
  "Total Tax Amount": "^(?:₹\\s?)?(\\d{1,3}(?:,\\d{3})*|\\d+)(\\.\\d{1,2})?(?:\\s?INR)?$"
}