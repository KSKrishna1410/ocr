-- Initialize database with required tables and comprehensive field data for OCR application

-- Create the t_icr_field_capture_data table
CREATE TABLE IF NOT EXISTS t_icr_field_capture_data (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    tenant_id INTEGER DEFAULT -1,
    doc_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the t_icr_field_keys table
CREATE TABLE IF NOT EXISTS t_icr_field_keys (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES t_icr_field_capture_data(id),
    key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert comprehensive INVOICE field configurations
INSERT INTO t_icr_field_capture_data (field_name, data_type, field_type, tenant_id, doc_type) VALUES
('Due Date', 'Date', 'Header', -1, 'INVOICE'),
('Invoice Date', 'Date', 'Header', -1, 'INVOICE'),
('CGST Tax Amount', 'Double', 'Header', -1, 'INVOICE'),
('CGST Tax Rate', 'Double', 'Header', -1, 'INVOICE'),
('Discount', 'Double', 'Header', -1, 'INVOICE'),
('Freight', 'Double', 'Header', -1, 'INVOICE'),
('IGST Tax Amount', 'Double', 'Header', -1, 'INVOICE'),
('IGST Tax Rate', 'Double', 'Header', -1, 'INVOICE'),
('Invoice Total Amount', 'Double', 'Header', -1, 'INVOICE'),
('Net Amount', 'Double', 'Header', -1, 'INVOICE'),
('SGST Tax Amount', 'Double', 'Header', -1, 'INVOICE'),
('SGST Tax Rate', 'Double', 'Header', -1, 'INVOICE'),
('Total Tax Amount', 'Double', 'Header', -1, 'INVOICE'),
('CIN Number', 'String', 'Header', -1, 'INVOICE'),
('GSTIN', 'String', 'Header', -1, 'INVOICE'),
('HSN', 'String', 'Header', -1, 'INVOICE'),
('Invoice Number', 'String', 'Header', -1, 'INVOICE'),
('IRN No', 'String', 'Header', -1, 'INVOICE'),
('PAN Number', 'String', 'Header', -1, 'INVOICE'),
('Payment Status', 'String', 'Header', -1, 'INVOICE'),
('PO No#', 'String', 'Header', -1, 'INVOICE'),
('Supplier Details', 'String', 'Header', -1, 'INVOICE'),
('Supplier Name', 'String', 'Header', -1, 'INVOICE'),
('Amount', 'Double', 'Line', -1, 'INVOICE'),
('Line Net Amount', 'Double', 'Line', -1, 'INVOICE'),
('Line Tax amt', 'Double', 'Line', -1, 'INVOICE'),
('Unit Price', 'Double', 'Line', -1, 'INVOICE'),
('Line Tax Percentage', 'Percent', 'Line', -1, 'INVOICE'),
('Description', 'String', 'Line', -1, 'INVOICE'),
('Line HSN', 'String', 'Line', -1, 'INVOICE'),
('Quantity', 'String', 'Line', -1, 'INVOICE'),
('Others', 'String', 'Others', -1, 'INVOICE'),
('table_end_position', 'String', 'Others', -1, 'INVOICE'),
('table_start_position', 'String', 'Others', -1, 'INVOICE');

-- Insert comprehensive BANKSTMT field configurations
INSERT INTO t_icr_field_capture_data (field_name, data_type, field_type, tenant_id, doc_type) VALUES
('Statement Date', 'Date', 'Header', -1, 'BANKSTMT'),
('Statement Date From', 'Date', 'Header', -1, 'BANKSTMT'),
('Statement Date To', 'Date', 'Header', -1, 'BANKSTMT'),
('Closing Balance', 'Double', 'Header', -1, 'BANKSTMT'),
('Opening Balance', 'Double', 'Header', -1, 'BANKSTMT'),
('Account Number', 'String', 'Header', -1, 'BANKSTMT'),
('Bank Branch', 'String', 'Header', -1, 'BANKSTMT'),
('IFSC Code', 'String', 'Header', -1, 'BANKSTMT'),
('Transaction Date', 'Date', 'Line', -1, 'BANKSTMT'),
('Value Date', 'Date', 'Line', -1, 'BANKSTMT'),
('Balance', 'Double', 'Line', -1, 'BANKSTMT'),
('Credit', 'Double', 'Line', -1, 'BANKSTMT'),
('Debit', 'Double', 'Line', -1, 'BANKSTMT'),
('Description', 'String', 'Line', -1, 'BANKSTMT'),
('Reference Number', 'String', 'Line', -1, 'BANKSTMT'),
('table_start_position', 'String', 'Others', -1, 'BANKSTMT');

-- Insert field keys for INVOICE fields (Due Date)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(1, 'Due Date');

-- Insert field keys for INVOICE fields (Invoice Date)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(2, 'Date'), (2, 'Dated'), (2, 'E-Invoice Ack.Date'), (2, 'Order Date'), (2, 'Invoice Date:'), 
(2, 'Invoice Date'), (2, 'BILL DATE'), (2, 'Date of Invoice'), (2, 'Date of Invoice:'), 
(2, 'Invoice date'), (2, 'Time'), (2, 'BILLDATE'), (2, 'Sale Date'), (2, 'Document Date'), (2, 'Date:');

-- Insert field keys for INVOICE fields (CGST Tax Amount)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(3, 'CGST9 (9%)'), (3, 'Add:CGST'), (3, 'CGST9%'), (3, 'CGST'), (3, 'CGST Amt'), 
(3, 'CGST(9%)'), (3, 'CGST Amount'), (3, 'Total CGST'), (3, 'ADD:CGST @ 9%'), 
(3, 'CGST @ 9%'), (3, '9%'), (3, 'CGST 9%'), (3, 'CGST 2.5%'), (3, 'AOD:CGST @ 9%');

-- Insert field keys for INVOICE fields (CGST Tax Rate)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(4, 'CGST%'), (4, 'CGST %'), (4, 'CG ST%');

-- Insert field keys for INVOICE fields (Discount)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(5, 'Discount/Margin*'), (5, 'DISCOUNT'), (5, 'Savings (Rs)'), (5, 'Discount/ Margin*'), 
(5, 'Total Savings'), (5, 'DISCOUNT()'), (5, 'Disc. %'), (5, 'Disc.'), (5, 'Qty(Disc)'), (5, '(15%)');

-- Insert field keys for INVOICE fields (Freight)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(6, 'Freight');

-- Insert field keys for INVOICE fields (IGST Tax Amount)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(7, 'IGST charged at 18%'), (7, 'IGST %'), (7, 'IGST 0%'), (7, 'IGST Amount/IGST Output @ 18%'), 
(7, 'Integrated GST (18%)'), (7, 'IGST5.0'), (7, 'Taxes: IGST @ 18%'), (7, 'IGST Amount'), 
(7, 'IGST Rate Amount'), (7, '@12%'), (7, 'IGST @ 18%'), (7, 'Total Tax Amount'), (7, '12%'), (7, 'IGST');

-- Insert field keys for INVOICE fields (IGST Tax Rate)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(8, 'IGST OUTPUT @ 18%'), (8, 'GST %');

-- Insert field keys for INVOICE fields (Invoice Total Amount)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(9, 'per'), (9, 'Totals'), (9, 'Balance Due'), (9, 'Invoice Value'), (9, 'Net Payable'), 
(9, 'Total'), (9, 'Total:'), (9, 'Total Invoice Value (in figure) '), (9, 'NETT AMOUNT (Rounded)'), 
(9, 'Total Invoice Value'), (9, 'Total in INR'), (9, 'Grand Total(incl. of taxes)'), (9, 'Grand Total'), 
(9, 'Amount Rs.'), (9, 'Total Value'), (9, 'Total Invoice Value (rounded off)'), (9, 'Rs.'), 
(9, 'Amount'), (9, 'Total Amount'), (9, 'Net Amount'), (9, 'Total Invoice Value (rounded off) '), 
(9, 'Current Total'), (9, 'TOTAL RECEIVED AMOUNT'), (9, 'Invoice Total Amount'), (9, 'Invoice Total'), 
(9, 'Item Total'), (9, 'GRAND TOTAL'), (9, 'Gross Amount/Total Invoice Value'), (9, 'Total Invoice Amount');

-- Insert field keys for INVOICE fields (Net Amount)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(10, 'Gross'), (10, 'Total Amount(+)'), (10, 'Amount(Rs.)'), (10, 'Total Taxable Value'), 
(10, 'Subtotal in INR'), (10, 'Amount'), (10, 'Total Amount Before Tax'), (10, 'Taxable Amount'), 
(10, 'Net Amount'), (10, 'Total MRP Value'), (10, 'Total Charges'), (10, 'Sub Total'), (10, 'Total Amt'), 
(10, 'Tax''ble Amt'), (10, 'AMT'), (10, 'Total MRP'), (10, 'Taxable '), (10, 'Item Total'), (10, 'Total'), 
(10, 'MRP (Rs) CGST'), (10, 'Amount Rs.'), (10, 'Taxable Value'), (10, 'Subtotal');

-- Insert field keys for INVOICE fields (SGST Tax Amount)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(11, 'Total SGST'), (11, 'SGST(9%)'), (11, 'SGST 9%'), (11, 'SGST'), (11, 'SGST9%'), 
(11, 'SCGT Amount'), (11, 'SGST Amount'), (11, 'SGST/UTGST 2.5%'), (11, 'Sgst @6%'), 
(11, 'SGST9 (9%)'), (11, '9%'), (11, 'Sgst @14%'), (11, 'Sgst @2.5%'), (11, 'SGST @ 9%'), 
(11, 'SGST Amt'), (11, 'ADD:SGST @ 9%'), (11, 'Add:SGST');

-- Insert field keys for INVOICE fields (SGST Tax Rate)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(12, 'SG ST%'), (12, 'SGST% ****'), (12, 'SGST %');

-- Insert field keys for INVOICE fields (Total Tax Amount)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(13, 'Total taxes'), (13, 'TaxAmt'), (13, 'Total Tax'), (13, 'Tax Amount'), (13, 'Tax Total');

-- Insert field keys for INVOICE fields (CIN Number)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(14, 'CIN');

-- Insert field keys for INVOICE fields (GSTIN)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(15, 'GSTIN No & Address:'), (15, 'GSTN No'), (15, 'Registration Number'), (15, 'GSTIN Number'), 
(15, 'GSTIN :-'), (15, 'GSTNo'), (15, 'GSTIN No'), (15, 'GSTN No :'), (15, 'GSTIN'), (15, 'GSTIN :'), 
(15, 'GSTN Numbe'), (15, 'GST No.'), (15, 'GST no of provider'), (15, 'GST Registration No'), 
(15, 'GST|N/U|N'), (15, 'GST'), (15, 'GST Tin'), (15, 'GSTN Number'), (15, 'GSTIN/UIN'), (15, 'GST No'), 
(15, 'GSTIN No.'), (15, 'Restaurant GSTIN');

-- Insert field keys for INVOICE fields (HSN)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(16, 'HSN/SAC'), (16, 'HSN/ SAC'), (16, 'and SAC code'), (16, 'SAC Code'), (16, 'HSN Code'), 
(16, 'HSN Code:'), (16, '/SAC'), (16, 'HSN');

-- Insert field keys for INVOICE fields (Invoice Number)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(17, 'Inv. No.'), (17, 'Invoice:#'), (17, 'Invoice Number #'), (17, 'lnvoice No,'), (17, 'No.'), 
(17, 'Invoice ID'), (17, 'Invoice Number#'), (17, 'Invoice #'), (17, 'Invoice #:'), (17, 'Invoice Serial Number'), 
(17, 'TAX INVOICE'), (17, 'Invoice No'), (17, 'Invoice#'), (17, 'Invoice#:'), (17, 'Tax Invoice No'), 
(17, 'Invoice No:'), (17, 'Document No'), (17, 'Order #'), (17, 'Bill No .'), (17, 'Inv No'), 
(17, 'Invoice No.'), (17, 'Invoice number'), (17, 'Invoice Number'), (17, 'Serial Invoice No'), 
(17, 'GST Invoice No.'), (17, 'Bill No'), (17, 'Document No.'), (17, 'Bill No.'), (17, 'OrderID / Bill No.'), 
(17, 'Number'), (17, 'I Invoice No.'), (17, 'Order No:'), (17, 'ORDER NUMBER:'), (17, 'Invoice');

-- Insert field keys for INVOICE fields (IRN No)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(18, 'IRN'), (18, 'IRN No'), (18, 'E-Invoice IRN No.');

-- Insert field keys for INVOICE fields (PAN Number)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(19, 'PAN Number'), (19, 'PAN'), (19, 'Company''s PAN'), (19, 'PAN No'), (19, 'PAN no.');

-- Insert field keys for INVOICE fields (Payment Status)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(20, 'Paid Via Other'), (20, 'Amount Paid'), (20, 'Amount Paid:'), (20, 'UPI Payment'), 
(20, 'CASH PAID'), (20, 'Amount Received From Customer'), (20, 'Paid'), (20, 'Paid Via Card'), 
(20, 'PaymentMode (Amount)'), (20, 'PAID'), (20, 'CREDIT CARD'), (20, 'Payment Method'), 
(20, 'Payment Method:'), (20, 'TOTAL RECEIVED AMOUNT'), (20, 'Mode of Payment'), (20, 'Payment Transaction ID:');

-- Insert field keys for INVOICE fields (PO No#)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(21, 'Order'), (21, 'Pur.Ord.No & Date/'), (21, 'Order Number'), (21, 'P.O. Number'), 
(21, 'Party''s PO No/Date'), (21, 'Order No'), (21, 'Dunzo Order:');

-- Insert field keys for INVOICE fields (Supplier Details)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(22, 'Billing /Supplier Information'), (22, 'Supply Address'), (22, 'Dispatch From'), 
(22, 'Sold By'), (22, 'Sold By / Seller'), (22, 'Details Of Supplier'), (22, 'Restaurant Address'), 
(22, 'Seller Details'), (22, 'Ship Address');

-- Insert field keys for INVOICE fields (Supplier Name)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(23, 'Seller Details'), (23, 'Sold By / Seller'), (23, 'Restaurant Name'), (23, 'Business Name'), 
(23, 'Sold By'), (23, 'Supply Address');

-- Insert field keys for BANKSTMT fields (Statement Date)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(33, 'Generated On'), (33, 'Statement Date'), (33, 'Statement Request/Download Date'), 
(33, 'Date'), (33, 'Date of Statement'), (33, 'Statement date'), (33, 'DATE');

-- Insert field keys for BANKSTMT fields (Statement Date From)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(34, 'STATEMENT PERIOD FROM'), (34, 'Transaction Date From'), (34, 'STATEMENT PERIOD'), 
(34, 'Statement From'), (34, 'From'), (34, '(From'), (34, 'Transaction Period'), 
(34, 'Statement Period From'), (34, 'Statement for the Period From'), (34, 'Detailed Statement for a/c no.'), 
(34, 'Period From'), (34, 'Period');

-- Insert field keys for BANKSTMT fields (Statement Date To)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(35, 'Transaction Period'), (35, 'STATEMENT PERIOD'), (35, 'To'), (35, 'Period To'), 
(35, 'Detailed Statement for a/c no.'), (35, 'Statement Period From'), (35, 'Statement To'), 
(35, 'Transaction Date To'), (35, 'Statement for the Period to'), (35, 'Statement from'), 
(35, 'Period'), (35, 'STATEMENT PERIOD TO');

-- Insert field keys for BANKSTMT fields (Closing Balance)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(36, 'Closing Bal'), (36, 'CLOSING BALANCE');

-- Insert field keys for BANKSTMT fields (Opening Balance)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(37, 'OPENING BALANCE'), (37, 'BROUGHT FORWARD');

-- Insert field keys for BANKSTMT fields (Account Number)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(38, 'Account No.'), (38, 'A/C No'), (38, 'Account No'), (38, 'Account Number - '), 
(38, 'ACCOUNT NO'), (38, 'Account Number'), (38, 'Statement of Account No'), 
(38, 'for Account Number'), (38, 'Account Number -'), (38, 'Statement of Axis Account No');

-- Insert field keys for BANKSTMT fields (Bank Branch)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(39, 'Branch Name'), (39, 'Account Branch'), (39, 'ACCOUNT BRANCH'), (39, 'Branch');

-- Insert field keys for BANKSTMT fields (IFSC Code)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(40, 'RTGS/NEFT IFSC'), (40, 'AFSC'), (40, 'IFSC CODE'), (40, 'IFSC Code'), (40, 'IFSC');

-- Insert field keys for BANKSTMT fields (Transaction Date)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(41, 'Post Date'), (41, 'Trans Date'), (41, 'Txn Date'), (41, 'DATE'), (41, 'Transaction Date'), (41, 'Tran Date');

-- Insert field keys for BANKSTMT fields (Value Date)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(42, 'VALUE DATE'), (42, 'Value Dt');

-- Insert field keys for BANKSTMT fields (Balance)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(43, 'BALANCE'), (43, 'Closing Balance'), (43, 'Balance(INR)');

-- Insert field keys for BANKSTMT fields (Credit)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(44, 'Deposit(Cr)'), (44, 'DEPOSITS'), (44, 'Type'), (44, 'Deposit Amt'), (44, 'CREDIT'), 
(44, 'Deposit (Cr)'), (44, 'Deposit Amt.'), (44, 'DR/CR'), (44, 'Withdrawal (Dr)/ Deposit (Cr)'), (44, 'DEPOSIT');

-- Insert field keys for BANKSTMT fields (Debit)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(45, 'WITHDRAWS'), (45, 'Withdrawals'), (45, 'Withdrawal Amt.'), (45, 'DR/CR'), (45, 'DEBIT'), 
(45, 'Type'), (45, 'Withdrawl (Dr)'), (45, 'Withdrawal (Dr)/ Deposit (Cr)');

-- Insert field keys for BANKSTMT fields (Description)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(46, 'Description'), (46, 'Narration'), (46, 'DESCRIPTION'), (46, 'Remarks'), (46, 'Transaction Remarks'), 
(46, 'Transaction'), (46, 'NARATION'), (46, 'Transaction Particulars'), (46, 'Particulars');

-- Insert field keys for BANKSTMT fields (Reference Number)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(47, 'Ref No'), (47, ' Cheque No/Reference '), (47, 'Cheque No'), (47, 'Chq./Ref.No.'), 
(47, 'REFERENCE NUMBER'), (47, 'Reference Number');

-- Insert field keys for BANKSTMT fields (table_start_position)
INSERT INTO t_icr_field_keys (field_id, key) VALUES
(48, 'Withdrawals'), (48, 'Transaction'), (48, 'Balance'), (48, 'Deposits'), (48, 'Txn Date');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_field_capture_tenant_doc ON t_icr_field_capture_data(tenant_id, doc_type);
CREATE INDEX IF NOT EXISTS idx_field_keys_field_id ON t_icr_field_keys(field_id); 