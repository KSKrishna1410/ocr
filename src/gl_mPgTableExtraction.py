import tabula
import pandas as pd
from tabula import read_pdf
import os
import re
import numpy as np
import csv
from src.gl_utilities import cleanTabulaData
# import pyPdf


def readPdf4Page(filepath,page):
    array_data=[]
    # Reading PDF using Table and get Dataframes
    rows_list = tabula.read_pdf(filepath,pages=page,silent=True,stream=True,lattice=True,guess=False,encoding='utf-8',pandas_options={"header": None})
        # area refers to the Portion of the page to analyze(top,left,bottom,right).
        # print('rows_list --->', rows_list)# Check if tabula extracted multiple tables
    if isinstance(rows_list, list) and len(rows_list)>0 :
        df = pd.concat(rows_list, ignore_index=True)
        df = df.dropna(how="all").dropna(axis=1, how="all")
        # Identify max columns available in structured data
        column_count = df.shape[1]
        threshold = column_count // 2  # Rows with at least 50% valid values
        # Keep only rows where non-null values are above the threshold
        df = df.dropna(thresh=threshold)
        df = df.dropna(how="all").dropna(axis=1, how="all")
        array_data = df.to_numpy()  # Convert to NumPy array
    else:
        print("❌ No table identified or extracted from PDF.")
    return array_data

# Function to check if a row contains header keywords (loose matching)
def is_header_row(row):
    row_stripped = row.astype(str).str.lower().str.strip()  # Convert to lowercase and strip spaces
    matched_count = sum(any(keyword.lower() in cell for cell in row_stripped) for keyword in expected_header)
    return matched_count >= len(expected_header) - 2  # Allow minor variations

print('multi page data extraction from Tabula ------> ')
def count_pdf_pages(file_path):
    rxcountpages = re.compile(rb"/Type\s*/Page([^s]|$)", re.MULTILINE|re.DOTALL)
    with open(file_path, "rb") as temp_file:
        return len(rxcountpages.findall(temp_file.read()))

def runTabuleProcess(folderpath):
    for file in os.listdir(folderpath):
        file_name = os.path.splitext(file)[0]
        print(f"Filename: {file_name}")
        if file.lower().endswith(".pdf"):
            filepath = os.path.join(folderpath, file)
            n = count_pdf_pages(filepath)
            print(f'multi page data  from {file_name}  and page count------> ', n)
            # if different pages have different areas from which data is to be extracted
            data = []
            folderpath += "\\"
            opPath = r'C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\sysGen_Invoices\Tabula_results'
            opPath += "\\"
            csv_output_path = opPath+file+'_allData.csv'
            with open(csv_output_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                for page in [str(i+1) for i in range(n)]:
                    pageData = readPdf4Page(filepath,page)
                    if len(pageData) > 0:
                        for eachrow in pageData:
                            writer.writerow(eachrow)
                            data.append(eachrow)
            print('Complete Extracted data lenght -------> ', len(data))
            print('Complete Extracted code -------> ', data)
            print(f"CSV file '{csv_output_path}' has been created successfully!")
            

def runTabuleProcess_main(folderpath):
    for file in os.listdir(folderpath):
        file_name = os.path.splitext(file)[0]
        print(f"Filename: {file_name}")
        if file.lower().endswith(".pdf"):
            filepath = os.path.join(folderpath, file)
            n = count_pdf_pages(filepath)
            print(f'multi page data  from {file_name}  and page count------> ', n)
            pageData = readPdf4Page(filepath,'all')
            if len(pageData) > 0:
                print('Complete Extracted data length -------> ', len(pageData))
                cleanTabulaData(folderpath,pageData,'invoice',file_name,'')

def runTabuleProcess_file(filepath):
    n = count_pdf_pages(filepath)
    # n = 1
    final_array = []
    print('multi pafe data frame from Tabula count------> ', n)
    # if different pages have different areas from which data is to be extracted
    pageData = readPdf4Page(filepath,'all')
    if(len(pageData)>0):
        print(f'Tabula All page captured output before cleaning-----> {pageData[0]}')
        print('Data type of the pageDate' , pageData)
        final_array.extend(pageData)
    return final_array

def runTabuleProcess_file_pageWise(filepath):
    n = count_pdf_pages(filepath)
    # n = 1
    final_array = []
    print('multi pafe data frame from Tabula count------> ', n)
    # if different pages have different areas from which data is to be extracted
    for page in [str(i+1) for i in range(n)]:
        pageData = readPdf4Page(filepath,page)
        if(len(pageData)>0):
            print(f'Tabula page {page} and captured output before cleaning-----> {pageData[0]}')
            print('Data type of the pageDate' , pageData)
            final_array.extend(pageData)
        # print(f'Tabula page {page} and captured output -----> {fixed_pages}')
        break
    return final_array

def main():
    folderpath = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\sysGen_Invoices\Processed"
    # filepath = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\tabula_bank_stmt\test\HDFC BANK.pdf"
    # file_name = os.path.splitext(os.path.basename(filepath))[0]
    # tableInfo = runTabuleProcess_file(filepath)
    # if len(tableInfo) > 0:  
    #     cleanTabulaData(folderpath,tableInfo,'BANKSTMT',file_name,'IDFC')
    runTabuleProcess_main(folderpath)
    
# main()