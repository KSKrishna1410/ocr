import tabula
import pandas as pd
from tabula import read_pdf
import os
import re
import numpy as np
import csv
from utilities import cleanTabulaData
# import pyPdf


def readPdf4Page(filepath,page):
    array_data=[]
    # Reading PDF using Table and get Dataframes
    rows_list = tabula.read_pdf(filepath,pages='all',silent=True,stream=True,lattice=True,guess=False,encoding='utf-8',pandas_options={"header": None})
                                #area refers to the Portion of the page to analyze(top,left,bottom,right).
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


def fix_column_mismatch(extracted_pages):
    """Ensures all extracted pages have the same number of columns."""
    if extracted_pages is None or len(extracted_pages) == 0:
        raise ValueError("Error: extracted_pages is empty. Cannot determine column count.")
    if isinstance(extracted_pages, np.ndarray):
        extracted_pages = extracted_pages.tolist()
    extracted_pages = [np.array(page) if not isinstance(page, np.ndarray) else page for page in extracted_pages]
    # Ensure all pages are at least 2D
    valid_pages = [page.reshape(1, -1) if page.ndim == 1 else page for page in extracted_pages if page.size > 0]
    if len(valid_pages) == 0:
        raise ValueError("Error: No valid pages found with data.")
    max_cols = valid_pages[0].shape[1]
    fixed_pages = []
    for page in extracted_pages:
        if page.size == 0:  
            fixed_pages.append(page)
            continue
        # Ensure page is 2D
        if page.ndim == 1:
            page = page.reshape(1, -1)
        # Convert to DataFrame
        df = pd.DataFrame(page)
        # Ensure column names are strings before applying .strip()
        df.columns = [str(col).strip() for col in df.columns]
        # If columns are missing, insert empty ones
        while df.shape[1] < max_cols:
            df.insert(df.shape[1], f"EmptyCol_{df.shape[1]}", np.nan)
        fixed_pages.append(df.to_numpy())
    return np.array(fixed_pages, dtype=object)


def fix_column_mismatch_old(extracted_pages):
    """Ensures all extracted pages have the same number of columns."""
    # Get max column count from the first page (assuming the first page is correct)
    max_cols = len(extracted_pages[0])
    # Extract column headers
    expected_headers = extracted_pages[0]  # First row of first page
    fixed_pages = []
    for page in extracted_pages:
        if len(page) == 0:
            fixed_pages.append(page)
            continue
        # Convert to DataFrame
        df = pd.DataFrame(page)
        # If columns are missing, insert empty ones
        while df.shape[1] < max_cols:
            df.insert(df.shape[1] - 1, f"EmptyCol_{df.shape[1]}", np.nan)
        fixed_pages.append(df.to_numpy())
    return fixed_pages

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
            csv_output_path = folderpath+file+'_TabulaData.csv'
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
            

def runTabuleProcess_file(filepath):
    n = count_pdf_pages(filepath)
    # n = 1
    final_array = []
    print('multi pafe data frame from Tabula count------> ', n)
    # if different pages have different areas from which data is to be extracted
    for page in [str(i+1) for i in range(n)]:
        pageData = readPdf4Page(filepath,page)
        if(len(pageData)>0):
            print(f'Tabula page {page} and captured output before cleaning-----> {pageData[0]}')
            fixed_pages = fix_column_mismatch(pageData)
            print('Data type of the pageDate' , pageData)
            final_array.extend(pageData)
            print('Data type of the fixed_pages' , type(fixed_pages))
        # print(f'Tabula page {page} and captured output -----> {fixed_pages}')
        break
    return final_array

def main():
    folderpath = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\tabula_bank_stmt\test"
    filepath = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\tabula_bank_stmt\test\axis-1.pdf"
    file_name = os.path.splitext(os.path.basename(filepath))[0]
    # tableInfo = runTabuleProcess_file(filepath)
    # if len(tableInfo) > 0:  
    #     cleanTabulaData(folderpath,tableInfo,'bankstmt',file_name,'')
    runTabuleProcess(folderpath)
    print (file_name)
    
main()