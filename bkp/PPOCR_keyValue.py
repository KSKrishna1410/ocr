# !pip install pdf2image
# !pip install PIL --no-cache-dir



# !pip install paddlepaddle paddleocr --upgrade


import os
from pdf2image import convert_from_path
from PIL import Image

from pdf2image import convert_from_path
from paddleocr import PaddleOCR
import numpy as np
import re
import json

# !apt-get install -y poppler-utils
# poppler_path = "/usr/bin/"
poppler_path = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\Release-24.08.0-0\poppler-24.08.0\Library\bin"

# from google.colab import drive
# drive.mount('/content/drive')

# file_path = '/content/drive/My Drive/ind_invoices/13.06.2024 Bajaj Electronics.pdf'
file_path = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\layoutlmv3-base\image\training_images\21.09.2024_shah_ghouse_hotel-1.png"
# image = Image.open(image_path)

# Check if the file exists
if not os.path.exists(file_path):
    print(f"❌ Error: File '{file_path}' not found. Please check the path.")
    exit()

# Identify file type
file_extension = os.path.splitext(file_path)[-1].lower()


ocr = PaddleOCR(use_angle_cls=True, lang="en")  # Supports multiple languages like "en", "ch", "hi"

def extract_key_value_pairs_old(paddle_ocr_output):
    key_value_pairs = {}
    keys = []
    values = []

    # Debug: Print the raw structure
    # print("Raw OCR Output:", json.dumps(paddle_ocr_output, indent=2))

    for entry in paddle_ocr_output:
        try:
            # Check if entry follows the expected pattern [[[bbox], (text, confidence)]]
            if isinstance(entry, list) and len(entry) > 0 and isinstance(entry[0], list):
                bbox, (text, confidence) = entry[0], entry[1]
                x_min, y_min = bbox[0]  # Top-left corner
                x_max, y_max = bbox[2]  # Bottom-right corner

                if text.strip().endswith(":"):  # Identify keys
                    keys.append((text.strip(), x_min, y_min, x_max, y_max))
                else:
                    values.append((text.strip(), x_min, y_min, x_max, y_max))
            else:
                print(f"Skipping malformed entry: {entry}")  # Debugging line

        except Exception as e:
            print(f"Error processing entry {entry}: {e}")

    # Match keys with nearest values
    for key, k_x_min, k_y_min, k_x_max, k_y_max in keys:
        closest_value = None
        min_distance = float("inf")

        for value, v_x_min, v_y_min, v_x_max, v_y_max in values:
            vertical_distance = v_y_min - k_y_max  # Check if below
            horizontal_distance = abs(v_x_min - k_x_min)  # Check alignment

            if vertical_distance > 0 and vertical_distance < min_distance:
                closest_value = value
                min_distance = vertical_distance

        key_value_pairs[key[:-1]] = closest_value  # Remove trailing ':'
    
    return key_value_pairs

    # key_list = ["Invoice No:", "Order ID:", "Date of Invoice:", "GSTIN:", "Customer Address:", "Restaurant Name:", "Restaurant GSTIN:", "Service Description:", "State:", "Place of Supply:", 
    #             "Category:", "HSN Code:","IGST", "CGST", "SGST/UTGST", "Total taxes", "Invoice Total"]

def extract_invoice_details(ocr_output):
    invoice_details = {}
    errors = []
    key_list = ["Invoice No:", "Order ID:", "Date of Invoice:", "GSTIN:", "Customer Address:", "Restaurant Name:", "Restaurant GSTIN:", "Service Description:", "State:", "Place of Supply:", "Category:", "HSN Code:", "IGST", "CGST", "SGST/UTGST", "Total taxes", "Invoice Total"]
    
    key_positions = {}
    value_positions = {}
    
    first_error_logged = False
    
    for item in ocr_output:
        bbox, text, confidence = item
        text = text.strip()
        
        if text in key_list:
            key_positions[text] = bbox  # Store bounding box for keys
        else:
            value_positions[text] = bbox  # Store bounding box for values
            if not first_error_logged:
                print("Error in item:", text)
                first_error_logged = True
            errors.append(text)
    
    for key, key_bbox in key_positions.items():
        closest_value = None
        min_distance = float("inf")
        
        for value, value_bbox in value_positions.items():
            distance = abs(key_bbox[0][0] - value_bbox[0][0]) + abs(key_bbox[0][1] - value_bbox[0][1])
            if distance < min_distance:
                min_distance = distance
                closest_value = value
                
        if closest_value:
            invoice_details[key] = closest_value
            del value_positions[closest_value]  # Avoid duplicate value assignment
    
    return invoice_details


def process_image_paddle(image):
    """
    Processes an image object (NumPy array) and extracts text using PaddleOCR,
    identifying key-value pairs and table data.
    """
    if image is None:
        print("❌ Error: Invalid image object")
        return

    # Convert image to NumPy array if it's not already
    if not isinstance(image, np.ndarray):
        image = np.array(image)

    # Perform OCR
    results = ocr.ocr(image, cls=True)
    print("Paddle Raw text output", results)

    # Extract text from results
    raw_text = " ".join([line[1][0] for result in results for line in result])

    # Print Extracted Raw Text
    print("\n🔹 Extracted Raw Text with PaddleOCR:\n")

    # Run extraction
    key_value_data = extract_invoice_details(results)

    # Print the extracted key-value pairs in JSON format
    print("\n🔹 Extracted key value data using PaddleOCR:\n", json.dumps(key_value_data, indent=4))

    # print(raw_text)
    # # Extract text and bounding boxes from results
    # extracted_data = [{"text": line[1][0], "bbox": line[0]} for result in results for line in result]
    
    # # Define possible keys for each field
    # key_mappings = {
    #     "invoice_number": ["invoice number", "serial invoice no", "invoice no", "order id"],
    #     "invoice_date": ["date", "invoice date", "bill date"],
    #     "invoice_amount": ["total amount", "invoice total", "amount due"],
    #     "supplier": ["supplier", "vendor", "company name"],
    #     "supplier_gst": ["supplier gst", "gst number", "tax id"]
    # }
    
    # # Identify key-value pairs
    # key_value_pairs = {}
    # key_value_pattern = re.compile(r"([\w\s]+):\s*(.+)", re.IGNORECASE)
    
    # for item in extracted_data:
    #     match = key_value_pattern.match(item["text"])
    #     if match:
    #         key, value = match.groups()
    #         key_value_pairs[key.strip().lower()] = value.strip()
    
    # # Map extracted key-value pairs to predefined structure
    # invoice_data = {key: None for key in key_mappings}
    
    # for field, possible_keys in key_mappings.items():
    #     for possible_key in possible_keys:
    #         if possible_key in key_value_pairs:
    #             invoice_data[field] = key_value_pairs[possible_key]
    #             break  # Stop checking once a match is found
    
    # # Identify table data based on bounding box alignment
    # table_data = []
    # table_rows = {}
    
    # for item in extracted_data:
    #     x1, y1, *_ = item["bbox"][0]  # Extract top-left corner
    #     row_key = y1 // 10  # Group by Y-axis proximity
    #     if row_key not in table_rows:
    #         table_rows[row_key] = []
    #     table_rows[row_key].append(item)
    
    # for row in sorted(table_rows.keys()):
    #     table_data.append([cell["text"] for cell in sorted(table_rows[row], key=lambda x: x["bbox"][0][0])])
    
    # # Print Extracted Key-Value Pairs
    # print("\n🔹 Extracted Key-Value Pairs:")
    # for key, value in key_value_pairs.items():
    #     print(f"{key}: {value}")
    
    # # Print Final Mapped Invoice Data
    # print("\n🔹 Mapped Invoice Data:")
    # print(invoice_data)
    
    # # Print Extracted Table Data
    # print("\n🔹 Extracted Table Data:")
    # for row in table_data:
    #     print(row)
    
    # return {"invoice_data": invoice_data, "table_data": table_data}




# Process based on file type
if file_extension == ".pdf":
    print(f"📄 Processing PDF: {file_path}")
    images = convert_from_path(file_path, poppler_path=poppler_path)

    if not images:
        print("❌ Error: No pages extracted from the PDF.")
        exit()

    print(f"✅ Loaded {len(images)} page(s) from: {file_path}")

    # Loop through PDF pages
    for page_num, image in enumerate(images, start=1):
        print(f"\n📄 Processing Page {page_num}...")
        process_image_paddle(image)

elif file_extension in [".jpg", ".jpeg", ".png"]:
    print(f"🖼️ Processing Image: {file_path}")
    image = Image.open(file_path)
    process_image_paddle(image)

else:
    print(f"❌ Error: Unsupported file format '{file_extension}'.")


