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
  }
]

bank_headers = {
    "ICICI Bank": [["SrNo", "TranID", "ValueDate", "TransactionDate", "Chequeno/RefNo",
                    "TransactionRemarks", "Withdrawl(Dr)", "Deposit(Cr)", "Balance"],['DATE', 'MODE**', 'PARTICULARS', 'DEPOSITS', 'WITHDRAWALS', 'BALANCE']],
    "Axis Bank": [["Txn Date", "Transaction", "Withdrawals", "Deposits", "Balance", "Other Information"],["Tran Date", "Chq No", "Particulars", "Debit", "Credit", "Balance", "Init.Br"]],
    "IDFC": [["TransactionDate", "Value Date", "Particulars", "ChequeNo", "Debit", "Credit", "Balance"]],
    "State Bank of India": [["Post Date", "Value Date", "Description", "ChequeNo/Reference", "Debit", "Credit", "Balance"]]
}