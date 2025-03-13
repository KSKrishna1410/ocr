import cv2
import numpy as np
import pytesseract
import pandas as pd

# Set the Tesseract path if required (Windows users may need this)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_table_from_image(image_path):
    # Load the image
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply adaptive threshold
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours from top to bottom
    # contours = sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[1])
    table_data = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        # Extract each cell
        if w > 30 and h > 20:  # Filter small contours
            cell = img[y:y + h, x:x + w]
            # Apply OCR to extract text
            text = pytesseract.image_to_string(cell, config='--psm 6').strip()
            print('Tesseract Results -------------->' , text)
            # Append text to table
            table_data.append((x, y, w, h, text))

    # Sort data into a structured table format
    # Group by rows based on y-coordinate proximity
    table_data = sorted(table_data, key=lambda x: (x[1] // 20, x[0]))  # Group similar y-values

    print('table_data--------->',table_data)
        # Organize extracted text into a structured table
    rows = {}
    for x, y, w, h, text in table_data:
        row_key = y // 20  # Group by similar y-values to approximate rows
        if row_key not in rows:
            rows[row_key] = []
        rows[row_key].append((x, text))
    
    # Sort each row by x-coordinate
    structured_data = []
    for key in sorted(rows.keys()):
        row = sorted(rows[key], key=lambda x: x[0])  # Sort by x-position
        structured_data.append([text for _, text in row])
    
    # Convert to a pandas DataFrame
    df = pd.DataFrame(structured_data)
    
    # Fill NaN values with empty strings for better readability
    df = df.fillna("")
    
    print("Extracted Table:")
    print(df.to_string(index=False, header=False))
    
    return df

# Run the function on an example image
filepath = r"C:\Users\nisha\Documents\runpod\tabDetected\hdfc-1.png" 
extract_table_from_image(filepath)
