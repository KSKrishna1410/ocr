


import tabula
import pandas as pd
from tabula import read_pdf
import os
import re
import numpy as np
# import pyPdf


folderpath = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\bank_stmt"
filename='ICICI-detailStatement.pdf'
folderpath += "\\"
filepath = folderpath+filename

# Output paths
csvname = filename+'tables_detected_cleaned1.csv'
jsonname = filename+'tables_detected_cleaned.json'
csv_output_path = folderpath+csvname
json_output_path = folderpath+jsonname

# Reading PDF using Table and get Dataframes
rows_list = tabula.read_pdf(filepath,pages='1',silent=True,stream=True,lattice=True,guess=False,encoding='utf-8')
                            #area refers to the Portion of the page to analyze(top,left,bottom,right).
print('Table extracted from tabula ----> ',len(rows_list) )

# Check if tabula extracted multiple tables
if isinstance(rows_list, list) and len(rows_list) > 0:
    # Merge all extracted tables into one DataFrame
    df = pd.concat(rows_list, ignore_index=True)
    print('Data Frame list --->', df)
    # **Clean column names** (Remove "\r" and spaces)
    df.columns = df.columns.str.replace(r'\r', '', regex=True).str.strip()
    print('Columns list --->', df.columns)
    # **Clean each cell's text** (Remove unwanted line breaks and extra spaces)
    df = df.applymap(lambda x: str(x).replace("\r", " ").strip() if isinstance(x, str) else x)

    # # Save as CSV (overwrite if exists)
    df.to_csv(csv_output_path, index=False)
    
    # # Save as JSON
    # df.to_json(json_output_path, orient="records", indent=4)

    # print(f"✅ CSV saved at: {csv_output_path}")
    # print(f"✅ JSON saved at: {json_output_path}")
else:
    print("❌ No table data extracted from PDF.")

print(f"✅ CSV saved at {csv_output_path}")

array_data = df.to_numpy()  # Convert to NumPy array

# Extracting Names (2nd column, index 1)
print('printing the 0 row--------------------------------> 0  ' ,array_data[0])
print('printing the 15 row--------------------------------> 15  ' ,array_data[14])
print('printing the 19 row--------------------------------> 19  ' ,array_data[19])
# for row in array_data:
#     print('printing the first row--------------------------------> ' ,row[1])  # row[1] corresponds to the 'Name' column

# rows_df = pd.DataFrame(rows_list,
#                        columns = ['Date','Particulars','Chq.No.','Withdrawals','Deposits',
#                                   'Auto Sweep','Reverse Sweep','Balance(INR)','Credit','Debit']) 
# Extract the first element to get a proper 2D list

      
#to count the no. of pages in a pdf
# print('multi pafe data frame from Tabula ------> ')
# def count_pdf_pages(file_path):
#     rxcountpages = re.compile(rb"/Type\s*/Page([^s]|$)", re.MULTILINE|re.DOTALL)
#     with open(file_path, "rb") as temp_file:
#         return len(rxcountpages.findall(temp_file.read()))
    
# n = count_pdf_pages(filepath)
# print('multi pafe data frame from Tabula count------> ', n)

# # if different pages have different areas from which data is to be extracted
# data = []
# for page in [str(i+1) for i in range(n)]:
#      data.append(
#                 tabula.read_pdf(filepath,pages=page,silent=True,stream=True,lattice=True,guess=False,encoding='utf-8')
#                 )
# print('multi page data frame from Tabula ------> ', data)