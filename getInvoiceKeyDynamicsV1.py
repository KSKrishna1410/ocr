import cv2
import numpy as np
from paddleocr import PaddleOCR
from fuzzywuzzy import fuzz, process  
from getKeys4OCRobj import *
import json
import math

# Initialize OCR with enhanced settings
ocr = PaddleOCR(use_angle_cls=True, lang='en', rec_algorithm='CRNN', det_db_box_thresh=0.5)

key_mapping = {
    "tax_amount": ["tax amount", "total tax", "tax payable", "gst amount", "Total taxes"],
    "supplier_name": ["Restaurant Name", "supplier name", "vendor name", "company name"],
    "supplier_gstin": ["GSTIN Number","supplier gstin", "supplier gst", "vendor gst number", "GSTIN/UIN", "Restaurant GSTIN","GSTIN: 36AAFCB7707D1ZV"],
    "supplier_details": ["supplier details", "vendor details", "seller info"],
    "sub_total_gst": ["sub total of gst", "gst subtotal", "total gst", "Sub Total"],
    "sgst_rate": ["sgst rate", "state gst rate","SGST/UTGST","SGST/"],
    "sgst_amount": ["sgst amount", "state gst amount"],
    "receiver_details": ["receiver details", "buyer details", "customer info"],
    "po_number": ["po no#", "purchase order number", "po number", "Order ID "],
    "pan_number": ["pan number", "permanent account number"],
    "irn_number": ["irn no", "invoice reference number"],
    "invoice_total_amount": ["invoice total amount", "grand total", "final amount", "Total","Invoice Total"],
    "invoice_number": ["Invoice#","invoice number","Invoice#", "Invoice no", "bill number"],
    "invoice_date": ["Dated","invoice date","Invoice Date", "date of invoice", "bill date"],
    "invoice_amount": ["invoice amount","Total", "total amount", "amount payable","Subtotal"],
    "igst_rate": ["igst rate", "integrated gst rate", "IGST", "IGST%", "IGST %"],
    "igst_amount": ["igst amount", "integrated gst amount"],
    "hsn_code": ["hsn code", "hsn"],
    "freight": ["freight", "shipping charges", "delivery charges"],
    "due_date": ["due date", "payment due date", "last payment date"],
    "discount": ["discount", "rebate", "price reduction"],
    "customer_name": ["customer name", "buyer name", "Buyer"],
    "customer_details": ["Customer Address"],
    "currency": ["currency", "invoice currency", "payment currency"],
    "cin_number": ["cin number", "corporate identification number"],
    "cgst_rate": ["cgst rate", "central gst rate","CGST"],
    "cgst_amount": ["cgst amount", "central gst amount"],
    "unit_price": ["unit price", "rate per unit", "price per item"],
    "unit": ["unit", "measurement unit"],
    "roundoff": ["roundoff", "rounding adjustment"],
    "quantity": ["quantity", "qty", "no. of items"],
    "promotion": ["promotion", "promo discount", "special offer"],
    "line_total": ["line total", "line amount", "subtotal per line"],
    "line_tax_percentage": ["line tax percentage", "tax rate per item"],
    "line_tax_amount": ["line tax amt", "line tax amount", "item tax"],
    "line_sgst_rate": ["line sgst rate", "state tax rate per item"],
    "line_sgst_amount": ["line sgst amount", "state tax amount per item"],
    "line_igst_rate": ["line igst rate", "integrated tax rate per item"],
    "line_igst_amount": ["line igst amount", "integrated tax amount per item"],
    "line_hsn": ["line hsn", "line hsn code"],
    "line_cgst_rate": ["line cgst rate", "central tax rate per item"],
    "line_cgst_amount": ["line cgst amount", "central tax amount per item"],
    "line_amount": ["line amount", "line item total"],
    "description": ["description", "item description", "product details"],
    "documentType": ["Document"]
}

def calculate_distance(bbox1, bbox2):
    """Calculate Euclidean distance between two bounding box centers."""
    x1, y1 = (bbox1[0][0] + bbox1[2][0]) / 2, (bbox1[0][1] + bbox1[2][1]) / 2
    x2, y2 = (bbox2[0][0] + bbox2[2][0]) / 2, (bbox2[0][1] + bbox2[2][1]) / 2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def generate_json_output(extracted_data):
    """Generate JSON output in the expected format."""
    output = []

    for key, value_data in extracted_data.items():
        key_bbox_cal = value_data["key_bbox"]
        value_bbox_cal = value_data["value_bbox"]
        key_bbox = json.dumps(value_data["key_bbox"])  # Convert list to string
        value_bbox = json.dumps(value_data["value_bbox"])  # Convert list to string
        matched_value = value_data["value"]

        closest_distance = calculate_distance(key_bbox_cal, value_bbox_cal)

        output.append({
            "key": key,
            "key_bounding_box": key_bbox,
            "matchedValue": matched_value,
            "valueBoundingBox": value_bbox,
            "closestDistance": closest_distance,
            "method": value_data["method"],
            "key_doc_text": value_data["doc_text"]
        })

    return json.dumps(output, indent=4)


def preprocess_image(image_path):
    """Enhances image for better OCR accuracy"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img

def extract_text(image_path):
    """Extracts text and bounding boxes from an image using PaddleOCR."""
    img = preprocess_image(image_path)
    result = ocr.ocr(img, cls=True)
    extracted_data = []
    print("\n🔹 PaddleOCR Raw Output:", result)

    doc_key_list_array = getKeylist(result, key_mapping)
    for key in doc_key_list_array:
        doc_key_list.append(key['key'])
    # print("\n🔹 document extracted Key list:", doc_key_list)
    for line in result:
        for word_info in line:
            bbox = word_info[0]  # Bounding box
            text = word_info[1][0].strip()  # Extracted text
            confidence = word_info[1][1]  # Confidence score
            extracted_data.append((text, bbox, confidence))
    
    return find_aligned_value(extracted_data, doc_key_list_array)

def match_key(text, key_list, threshold=85):
    best_match, score = process.extractOne(text.lower(), key_list)
    return best_match if score >= threshold else None

def get_x_y_positions_ctr(bbox):
    """Computes the average X and Y positions of a bounding box."""
    x_center = (bbox[0][0] + bbox[2][0]) / 2
    y_center = (bbox[0][1] + bbox[2][1]) / 2
    return x_center, y_center

def get_x_y_positions(bbox):
    """Returns the rightmost X position (end of key) and top Y position."""
    key_end_x = max(bbox[0][0], bbox[1][0], bbox[2][0], bbox[3][0])  # Rightmost X-coordinate
    top_y = min(bbox[0][1], bbox[1][1], bbox[2][1], bbox[3][1])  # Top Y-coordinate
    return key_end_x, top_y

def find_aligned_value(extracted_data, key_info_list, y_tolerance=20):
    """Finds key-value pairs where the value is directly to the right of the key."""
    keys = []
    values = []
    
    # Step 1: Categorize extracted text into keys and values
    for entry in extracted_data:
        text, bbox, confidence = entry
    
        # Find if the extracted text matches any key
        matched_key_entry = next((key_entry for key_entry in key_info_list if key_entry["key"].lower() == text.lower()), None)
        if matched_key_entry and matched_key_entry["key_bounding_box"]:
            keys.append((matched_key_entry["standard_key"], eval(matched_key_entry["key_bounding_box"]), text))
        else:
            values.append((text, bbox))
    
    # Step 2: Sort by Y first, then X for better alignment detection
    keys.sort(key=lambda x: (x[1][0][1], x[1][0][0]))  # Sort by Y, then X
    values.sort(key=lambda x: (x[1][0][1], x[1][0][0]))
    bottom_tolerance = 20  # Adjust as needed
    
    # Step 3: Matching the paired value for the given key
    key_value_pairs = []
    capturedMethod = None
    for eachKey in key_info_list:
        key_text = eachKey['standard_key']
        if eachKey["key_bounding_box"] is not None and eachKey["value"] is None:
            key_bbox = json.loads(eachKey['key_bounding_box'])
            key_x1, key_y1 = key_bbox[0]  # Top-left of key
            key_x2, key_y2 = key_bbox[1]  # Top-right of key
            key_x3, key_y3 = key_bbox[2]  # bottom-right of key
            key_x4, key_y4 = key_bbox[3]  # bottom-left of key
            closest_value = None
            min_x_distance = float('inf')
            min_y_distance = float('inf')
            # Right aliged side and within Y tolerance
            for val_text, val_bbox in values:
                val_x1, val_y1 = val_bbox[0]  # Top-left of value
                val_x2, val_y2 = val_bbox[1]  # Top-right of value

                # Ensure value is on the right side and within Y tolerance
                if val_x1 > key_x2 and abs(val_y1 - key_y1) <= y_tolerance:
                    x_distance = val_x1 - key_x2  # Distance between key end and value start

                    if x_distance < min_x_distance:
                        min_x_distance = x_distance
                        closest_value = val_text
                        closest_bbox = val_bbox
                        capturedMethod =  'right_aligned_pair'
                        closest_distance = calculate_distance(key_bbox, closest_bbox)
                        if closest_value and closest_distance < 1200:
                            # key_value_pairs[key_text] = {
                            #     "value": closest_value,
                            #     "key_bbox": key_bbox,
                            #     "value_bbox": closest_bbox,
                            #     "method": capturedMethod,
                            #     "doc_text" : eachKey['key']
                            # }
                            key_value_pairs.append({
                                "key":key_text,
                                "value": closest_value,
                                "key_bbox": key_bbox,
                                "value_bbox": closest_bbox,
                                "method": capturedMethod,
                                "doc_text" : eachKey['key'],
                                "closest_distance" : closest_distance
                            })
                if (key_y3 < val_y1 <= key_y3 + bottom_tolerance) and (key_x1 - bottom_tolerance <= val_x1 and key_x2 >= val_x1):
                    y_distance = val_y1 - key_y3  # Distance between key bottom and value top

                    if y_distance < min_y_distance:  # Choose the closest vertical match
                        min_y_distance = y_distance
                        closest_value = val_text
                        closest_bbox = val_bbox
                        capturedMethod =  'bottom_aligned_pair'
                        closest_distance = calculate_distance(key_bbox, closest_bbox)
                        if closest_value:
                            key_value_pairs.append({
                                "key":key_text,
                                "value": closest_value,
                                "key_bbox": key_bbox,
                                "value_bbox": closest_bbox,
                                "method": capturedMethod,
                                "doc_text" : eachKey['key'],
                                "closest_distance" : closest_distance
                            })
        
        elif eachKey["value"] is not None:
            print(f"Bounding Box matching if value found-> '{key_text}")
            key_value_pairs.append({
                "key":key_text,
                "value": eachKey["value"],
                "key_bbox": json.loads(eachKey['key_bounding_box']),
                "value_bbox": json.loads(eachKey['key_bounding_box']),
                "method": 'colon_identification',
                "doc_text" : eachKey['key']
            })
    return key_value_pairs

def process_invoice(image_path):
    """Extracts key-value pairs from an invoice image."""
    extracted_data = extract_text(image_path)
    print("\n🔹 Extracted Key-Value Pairs:")
    for obj in extracted_data:
        print(f"{obj['key']} → {obj['value']}")
    # json_output = generate_json_output(extracted_data)
    extracted_data = json.dumps(extracted_data, indent=4)
    
    print(extracted_data)
    # return extracted_data

if __name__ == "__main__":

    # Right Aligned key_value
    # image_path = r"document/sree_cammphor_works-1.png"
    # image_path = r"document/iteminvoicedownload-11.png"
    # image_path = r"document/21.09.2024_shah_ghouse_hotel-1.png"
    # image_path = r"document/amazon_invoice_(1)-1.png"
    # image_path = r"document/13.05.2024__digital_track-1.png"
    
    # Bottom Aligned key_value
    image_path = r"document/15.04.2024_global_technologies-1.png"
    
    doc_key_list = []
    process_invoice(image_path)
