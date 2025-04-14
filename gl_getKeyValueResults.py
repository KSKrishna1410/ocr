import cv2
import numpy as np
from paddleocr import PaddleOCR
from fuzzywuzzy import fuzz, process  
from getKeys4OCRobj import *
import json
import math
import os
import csv
from gl_utilities import save_extracted_data, upload_to_sftp, save_extracted_data_remote
import statistics

# Initialize OCR with enhanced settings
ocr = PaddleOCR(use_angle_cls=True, lang='en', rec_algorithm='CRNN', det_db_box_thresh=0.5)
csv_file = "extracted_batch_data.csv"

doc_key_list = []
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

# def analyze_text_with_ai(text, task="Give me the Invoice details"):
#     query = f"{task} this document:\n\n{text}"
#     response = ollama.chat(model="mistral", messages=[{"role": "user", "content": query}])
#     return response['message'] if response else "AI processing failed."
 
def extract_text(image_path,doc_name,output_folder,keyMappingData):
    """Extracts text and bounding boxes from an image using PaddleOCR."""
    img = preprocess_image(image_path)
    result = ocr.ocr(img, cls=True)
    rawtxtResult = result
    # print("\n🔹 PaddleOCR Raw Output:", result)
    if result is None or result == [None]:  # Handle empty or None result
        # error_log_path = os.path.join(output_folder, "error_report.txt")

        with open(error_log_path, "a", encoding="utf-8") as error_file:
            error_file.write(f"❌ Failed to process: {image_path}\n")

        print(f"❌ OCR extraction failed for {image_path}. Logged in error report.")
        return []  # Return empty extracted_data to prevent failure
    extracted_data = []
    extracted_rawText = []
    for eachResult in result:
        for line in eachResult:
            text = line[1][0]
            bbox = line[0] if len(line[0]) == 4 else None  # Ensure bbox has four points
            if bbox:
                extracted_rawText.append({"text": text, "bbox": bbox})
    # print("\n🔹 PaddleOCR Raw Output:", result)
    # Convert raw text to bytes for uploading
    raw_text_content = "\n".join(data["text"] for data in extracted_rawText).encode("utf-8")
    raw_txt_file = f"{doc_name}_paddleocr_rawtxt.txt"
    upload_to_sftp(raw_text_content, raw_txt_file, output_folder)
    print(f"✅ Extracted raw text uploaded to SFTP: {raw_txt_file}")

    # Convert OCR result (JSON) to bytes
    ocr_json_content = json.dumps(result, indent=4, ensure_ascii=False).encode("utf-8")
    ocr_result_file = f"{doc_name}_paddleocr_result.txt"
    upload_to_sftp(ocr_json_content, ocr_result_file, output_folder)
    print(f"✅ OCR result JSON uploaded to SFTP: {ocr_result_file}")
    
    
    # output_txt_path = os.path.join(output_folder, f"{doc_name}_paddleocr_result.txt")  # Save in output folder
    # output_rawtxt_path = os.path.join(output_folder, f"{doc_name}_paddleocr_rawtxt.txt")  # Save in output folder
    
    # # To Save raw text in a file
    # with open(output_rawtxt_path, "w", encoding="utf-8") as f:
    #     f.writelines(data["text"] + "\n" for data in extracted_rawText)  # Dump all text at once
    # print(f"Extracted text saved to: {output_rawtxt_path}")

    # # Save OCR result to a text file
    # with open(output_txt_path, "w", encoding="utf-8") as f:
    #     json.dump(result, f, indent=4, ensure_ascii=False)

    # print(f"✅ OCR result saved at: {output_txt_path}")
    if not keyMappingData:  keyMappingData = key_mapping
    print('keyMappingData Generated: ', keyMappingData)
    # print("\n🔹 PaddleOCR Raw Output:", result)
    doc_key_list_array = getKeylist(result, keyMappingData)
    for key in doc_key_list_array:
        doc_key_list.append(key['key'])
    # print("\n🔹 document extracted Key list:", doc_key_list)
    for line in result:
        for word_info in line:
            bbox = word_info[0]  # Bounding box
            # print(' Casting issue debug bbox word_info[0]', word_info[0])
            # print(' Casting issue debug text', word_info[1][0])
            text = word_info[1][0].strip()  # Extracted text
            # text = word_info[1][0].strip() if isinstance(word_info[1][0], str) else str(word_info[1][0]) if isinstance(word_info[1][0], (float, int)) else word_info[1][0]
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
    """Finds key-value pairs where the value is directly to the right of the key or just below it."""
    import statistics, json

    keys = []
    values = []

    # Step 1: Categorize extracted text into keys and values
    for entry in extracted_data:
        text, bbox, confidence = entry
        matched_key_entry = next((key_entry for key_entry in key_info_list if key_entry["key"].lower() == text.lower()), None)
        if matched_key_entry and matched_key_entry["key_bounding_box"]:
            keys.append((matched_key_entry["standard_key"], eval(matched_key_entry["key_bounding_box"]), text))
        else:
            values.append((text, bbox))

    # Step 2: Sort by Y first, then X for better alignment detection
    keys.sort(key=lambda x: (x[1][0][1], x[1][0][0]))
    values.sort(key=lambda x: (x[1][0][1], x[1][0][0]))

    key_value_pairs = []
    print('key_info_list Values before Loop ---> ', key_info_list)

    used_value_bboxes = []  # Track matched values to prevent re-use

    for eachKey in key_info_list:
        key_text = eachKey['standard_key']
        if eachKey["key_bounding_box"] is not None and eachKey["value"] is None:
            key_bbox = json.loads(eachKey['key_bounding_box'])
            key_x1, key_y1 = key_bbox[0]  # Top-left
            key_x2, key_y2 = key_bbox[1]  # Top-right
            key_x3, key_y3 = key_bbox[2]  # Bottom-right
            key_x4, key_y4 = key_bbox[3]  # Bottom-left

            closest_value = None
            min_x_distance = float('inf')
            min_y_distance = float('inf')

            # Right aligned matching
            for val_text, val_bbox in values:
                if val_bbox in used_value_bboxes:
                    continue  # Skip reused values
                val_x1, val_y1 = val_bbox[0]
                val_x2, val_y2 = val_bbox[1]

                average = statistics.mean([key_x1, key_x2])
                if val_x1 > average and abs(val_y1 - key_y1) <= y_tolerance:
                    x_distance = val_x1 - key_x2
                    if x_distance < min_x_distance:
                        min_x_distance = x_distance
                        closest_value = val_text
                        closest_bbox = val_bbox
                        capturedMethod = 'right_aligned_pair'
                        closest_distance = calculate_distance(key_bbox, closest_bbox)
                        print('Right-aligned match candidate:', key_text, '-->', val_text, 'with distance', closest_distance)
                        existing_index = next((i for i, kv in enumerate(key_value_pairs) if kv["key"] == key_text), None)
                        for threshold in range(100, 1601, 100):
                            if closest_value and closest_distance < threshold:
                                if existing_index is None:
                                    key_value_pairs.append({
                                        "key": key_text,
                                        "value": closest_value,
                                        "key_bbox": key_bbox,
                                        "value_bbox": closest_bbox,
                                        "method": capturedMethod,
                                        "doc_text": eachKey['key'],
                                        "closest_distance": closest_distance
                                    })
                                    used_value_bboxes.append(closest_bbox)
                                    print(f"[RIGHT] Matched {key_text} --> {closest_value} within threshold {threshold}: Distance = {closest_distance}")
                                    break
                                else:
                                    # If it exists, only replace if new distance is smaller
                                    existing_distance = key_value_pairs[existing_index]["closest_distance"]
                                    if closest_distance < existing_distance:
                                        # Replace the existing entry
                                        key_value_pairs[existing_index] = {
                                            "key": key_text,
                                            "value": closest_value,
                                            "key_bbox": key_bbox,
                                            "value_bbox": closest_bbox,
                                            "method": capturedMethod,
                                            "doc_text": eachKey['key'],
                                            "closest_distance": closest_distance
        }

            # Bottom aligned matching with gradual bottom_tolerance Tolerance method
            # for bottom_tolerance in range(10, 51, 10):
            #     for val_text, val_bbox in values:
            #         if val_bbox in used_value_bboxes:
            #             continue  # Skip reused values
            #         val_x1, val_y1 = val_bbox[0]
            #         if (key_y3 < val_y1 <= key_y3 + bottom_tolerance) and (key_x1 - bottom_tolerance <= val_x1 <= key_x2):
            #             y_distance = val_y1 - key_y3
            #             if y_distance < min_y_distance:
            #                 min_y_distance = y_distance
            #                 closest_value = val_text
            #                 closest_bbox = val_bbox
            #                 capturedMethod = 'bottom_aligned_pair'
            #                 closest_distance = calculate_distance(key_bbox, closest_bbox)
            #                 print(f"Bottom-aligned match candidate for {key_text} --> {val_text} at tolerance {bottom_tolerance}: Distance = {closest_distance}")
            #                 if closest_value and closest_distance < bottom_tolerance:
            #                     key_value_pairs.append({
            #                         "key": key_text,
            #                         "value": closest_value,
            #                         "key_bbox": key_bbox,
            #                         "value_bbox": closest_bbox,
            #                         "method": capturedMethod,
            #                         "doc_text": eachKey['key'],
            #                         "closest_distance": closest_distance
            #                     })
            #                     used_value_bboxes.append(closest_bbox)
            #                     break  # Stop once matched within a tolerance
            #     else:
            #         continue  # Continue outer loop only if inner did not break
            #     break  # Break outer loop if matched

            # Bottom aligned matching with gradual bottom_tolerance
            actual_bottom_threshold = 60  # Define your bottom threshold
            match_found = False
            match_candidates = []
            for val_text, val_bbox in values:
                if val_bbox in used_value_bboxes:
                    continue  # Skip reused values

                val_x1, val_y1 = val_bbox[0]

                if (key_y3 < val_y1 <= key_y3 + actual_bottom_threshold) and (key_x1 - actual_bottom_threshold <= val_x1 <= key_x2):
                    print(f"[Bottom] initiating Bottom Method {key_text} --> {val_text}")
                    y_distance = val_y1 - key_y3
                    print(f"[Y Distance] in Bottom Method {y_distance} and the min_y_dist {min_y_distance}")

                    if y_distance < min_y_distance:
                        min_y_distance = y_distance
                        closest_value = val_text
                        closest_bbox = val_bbox
                        capturedMethod = 'bottom_aligned_pair'
                        closest_distance = calculate_distance(key_bbox, closest_bbox)
                        print(f"Bottom-aligned match candidate for {key_text} --> {val_text}: Distance = {closest_distance}")

                        if closest_value and closest_distance < actual_bottom_threshold:
                            key_value_pairs.append({
                                "key": key_text,
                                "value": closest_value,
                                "key_bbox": key_bbox,
                                "value_bbox": closest_bbox,
                                "method": capturedMethod,
                                "doc_text": eachKey['key'],
                                "closest_distance": closest_distance
                            })
                            print(f"✅ Bottom KVP-aligned match for {key_text} --> {val_text}")
                            used_value_bboxes.append(closest_bbox)
                            match_found = True
                            break  # Stop checking once a valid match is found

        elif eachKey["value"] is not None:
            print(f"Colon match used for: '{key_text}'")
            key_value_pairs.append({
                "key": key_text,
                "value": eachKey["value"],
                "key_bbox": json.loads(eachKey['key_bounding_box']),
                "value_bbox": json.loads(eachKey['key_bounding_box']),
                "method": 'colon_identification',
                "doc_text": eachKey['key']
            })

    # Step 3: GST Pattern Matching
    gst_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b'
    for entry in extracted_data:
        text, bbox, confidence = entry
        matches = re.findall(gst_pattern, text)
        for match in matches:
            print(f"[GST MATCH] Found GST: {match} in text: {text}")
            key_value_pairs.append({
                "key": "GST No",
                "value": match,
                "key_bbox": bbox,
                "value_bbox": bbox,
                "method": "gst_regex_match",
                "doc_text": text
            })
    return key_value_pairs


############################################################################################

def process_document(image_path, doc_name, opfldr, keyMappingData):
    print('Inside Process function for Document' , doc_name)
    """Extracts key-value pairs from an invoice image."""
    extracted_data = extract_text(image_path, doc_name,opfldr,keyMappingData)
    # save_extracted_data(extracted_data, opfldr, doc_name)
    save_extracted_data_remote(extracted_data, opfldr, doc_name)
    # json_output = generate_json_output(extracted_data)
    extracted_data = json.dumps(extracted_data, indent=4)
    return extracted_data

def ProcessFile():
    print('Inside Process function')