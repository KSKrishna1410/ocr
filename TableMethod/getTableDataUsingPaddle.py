from paddleocr import PaddleOCR
import cv2
import pandas as pd
import numpy as np

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang="en")

# Load Image (Replace 'image_path' with actual file path)
image_path = r"C:\Users\nisha\Documents\runpod\tabDetected\hdfc-1.png" 
image = cv2.imread(image_path)

# Run OCR on Image
results = ocr.ocr(image_path, cls=True)

# Process OCR results
table_data = []
for line in results:
    for word in line:
        text = word[1][0]  # Extract detected text
        table_data.append(text)

# Manually identify column breaks based on the extracted text format
columns = ["Date", "Description", "RefNo", "Value Date", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"]

# Convert to Pandas DataFrame
num_columns = len(columns)
table_rows = [table_data[i : i + num_columns] for i in range(0, len(table_data), num_columns)]
print('Table_rows ------> ', table_rows)
df = pd.DataFrame(table_rows, columns=columns)

# Print the extracted table
print(df.to_string(index=False))