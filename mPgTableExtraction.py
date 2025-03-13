import tabula
import pandas as pd
from tabula import read_pdf
import os
import re
# import numpy as np
import csv
# import pyPdf


folderToProcess = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\tabula_bank_stmt"
filename = None
folderToProcess += "\\"

def readPdf4Page(filepath,page):
    array_data=[]
    # Reading PDF using Table and get Dataframes
    rows_list = tabula.read_pdf(filepath,pages=page,silent=True,stream=True,lattice=True,guess=False,encoding='utf-8',pandas_options={"header": None})
                                #area refers to the Portion of the page to analyze(top,left,bottom,right).

    # print('rows_list --->', rows_list)# Check if tabula extracted multiple tables
    if isinstance(rows_list, list) and len(rows_list)>0 :
        df = pd.concat(rows_list, ignore_index=True)
        array_data = df.to_numpy()  # Convert to NumPy array
        print('length of array_data ----> ',array_data[0])
        
    else:
        print("❌ No table identified or extracted from PDF.")
    return array_data
# readPdf4Page(3)


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
            print('multi pafe data frame from Tabula count------> ', n)

            # if different pages have different areas from which data is to be extracted
            data = []
            csv_output_path = folderpath+file+'allData.csv'
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
            
def runTabuleProcess_file(folderpath,filepath,file):
    n = count_pdf_pages(filepath)
    print('multi pafe data frame from Tabula count------> ', n)

    # if different pages have different areas from which data is to be extracted
    data = []
    # csv_output_path = os.path.join(folderpath, file,'allData.csv')
    csv_output_path = folderpath+file+'allData.csv'
    with open(csv_output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for page in [str(i+1) for i in range(n)]:
            pageData = readPdf4Page(filepath,page)
            if len(pageData) > 0:
                for eachrow in pageData:
                    writer.writerow(eachrow)
                    data.append(eachrow)
    return data

# runTabuleProcess(folderToProcess)