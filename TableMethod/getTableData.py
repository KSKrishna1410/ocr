from paddleocr import PaddleOCR
import numpy as np
from tabulate import tabulate

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang="en")  

# Perform OCR on the image
# output_folder = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\docs\images"  # Folder to save PNGs
img_path = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\inputs\13.05.2024__digital_track-1.png"
result = ocr.ocr(img_path, cls=True)

# Function to group text into tables based on bounding boxes
def extract_tables(ocr_result):
    table_data = []

    for page in ocr_result:
        words = []
        
        for line in page:
            if len(line) == 2:  # Handle missing confidence score
                bbox, text = line
            elif len(line) == 3:  # Normal case
                bbox, text, _ = line
            else:
                continue  # Skip malformed data
            
            x_min, y_min = bbox[0]  # Top-left corner
            x_max, y_max = bbox[2]  # Bottom-right corner
            
            words.append({
                "text": text[0] if isinstance(text, list) else text,
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_max,
                "y_max": y_max
            })
        
        words.sort(key=lambda word: word["y_min"])

        table = []
        current_row = []
        prev_y = None
        row_threshold = 10  

        for word in words:
            if prev_y is not None and abs(word["y_min"] - prev_y) > row_threshold:
                # Extract only text, sort by x_min for correct column order
                table.append([w["text"] for w in current_row])
                current_row = []

            current_row.append(word)
            prev_y = word["y_min"]

        if current_row:
            table.append([w["text"] for w in current_row])

        table_data.append(table)

    return table_data

def extract_tables_new(ocr_result):
    table_data = []
    
    for page in ocr_result:
        words = []
        for line in page:
            if len(line) == 2:  # Ensure correct unpacking
                bbox, text_info = line
                text, _ = text_info  # Extract text and ignore confidence score
                x_min, y_min = bbox[0]  # Top-left corner
                x_max, y_max = bbox[2]  # Bottom-right corner
                
                words.append({
                    "text": text,
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max
                })
        
        # Sort words by y_min (row-wise order)
        words.sort(key=lambda word: word["y_min"])
        
        table = []
        current_row = []
        prev_y = None
        
        for word in words:
            if prev_y is None or abs(word["y_min"] - prev_y) < 10:  # Threshold to detect row changes
                current_row.append(word["text"])
            else:
                table.append(current_row)
                current_row = [word["text"]]
            
            prev_y = word["y_min"]
        
        if current_row:
            table.append(current_row)

        table_data.append(table)
    
    return table_data


# # Extract tables from OCR result
# tables = extract_tables(result)
# print('Table data ----> ', tables)  # Print in a tabular format
# # Print extracted table data
# for table_index, table in enumerate(tables):
#     print(f"Table {table_index + 1}:")
#     for row in table:
#         print("\t".join(map(str, row)))  # Convert elements to strings before joining
#     print("\n" + "="*50 + "\n")

# Extract tables
tables = extract_tables(result)
print("\nExtracted Table Data:")

# Print each table using tabulate
for table_index, table in enumerate(tables):
    print(f"\nTable {table_index + 1}:")
    print(tabulate(table, tablefmt="grid"))  # Prints in a grid format for better visualization
    print("\n" + "="*50 + "\n")