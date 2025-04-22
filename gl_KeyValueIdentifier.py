import cv2
import numpy as np
import json
import math
import os
import csv
import re
import statistics

from PIL import Image
from fuzzywuzzy import fuzz, process  
from paddleocr import PaddleOCR, draw_ocr

from getKeys4OCRobj import getKeylist
from gl_utilities import save_extracted_data, upload_to_sftp, save_extracted_data_remote
from tableMarkingDetection import OCRBoxDrawer, TableDetector
from gl_mistral import analyze_text_with_ai
from generateKey_mapping import documentClassifier, generate_key_mapping_remote



from gl_constants import regex_check
# Initialize OCR with enhanced settings
ocr = PaddleOCR(use_angle_cls=True, lang='en', rec_algorithm='CRNN', det_db_box_thresh=0.5)

class OCRExtractorAndSaver:
    
    def __init__(self, image_path, doc_name, output_folder):
        self.image_path = image_path
        self.doc_name = doc_name
        self.output_folder = output_folder
        self.ocr = ocr
        self.sftp_uploader = upload_to_sftp
        self.result = []
        self.extracted_data = []
        self.raw_text = ""
        
    def preprocess_image(self):
        """Enhances image for better OCR accuracy"""
        img = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.GaussianBlur(img, (5, 5), 0)
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return img
    

    def perform_ocr_and_save(self):
        # img = preprocess_image(self.image_path)
        self.result = self.ocr.ocr(self.image_path, cls=True)
        # print('OCR Ext ->' , self.result)
        if not self.result or self.result == [None]:
            error_log_path = os.path.join(self.output_folder, "error_report.txt")
            with open(error_log_path, "a", encoding="utf-8") as error_file:
                error_file.write(f"❌ Failed to process: {self.image_path}\n")
            print(f"❌ OCR extraction failed for {self.image_path}. Logged in error report.")
            return False

        self.raw_text = "\n".join(line[1][0] for result in self.result for line in result)
        # self.extracted_data = [
        #     (line[1][0].strip(), line[0], line[1][1])
        #     for result in self.result for line in result
        # ]

        self._save_raw_text()
        self._save_ocr_json()
        return True

    def _save_raw_text(self):
        content = self.raw_text.encode("utf-8")
        raw_txt_file = f"{self.doc_name}_paddleocr_rawtxt.txt"
        self.sftp_uploader(content, raw_txt_file, self.output_folder)
        print(f"✅ Extracted raw text uploaded to SFTP: {raw_txt_file}")

    def _save_ocr_json(self):
        ocr_json_content = json.dumps(self.result, indent=4, ensure_ascii=False).encode("utf-8")
        ocr_result_file = f"{self.doc_name}_paddleocr_result.txt"
        self.sftp_uploader(ocr_json_content, ocr_result_file, self.output_folder)
        print(f"✅ OCR result JSON uploaded to SFTP: {ocr_result_file}")
    

class DocumentAnalyzer:
    def __init__(self, doc_name, image_path, result, raw_text, key_mapping_data, sftp_uploader, remote_path):
        self.doc_name = doc_name
        self.image_path = image_path
        self.result = result
        self.raw_text = raw_text
        self.key_mapping_data = key_mapping_data
        self.remote_path = remote_path
        self.sftp_uploader = sftp_uploader
        self.doc_key_list_array = []
        self.doc_key_list = []
        self.keyValueData = []
        self.actual_doc_type = None
        # self.sortedOCRresult = []
        self.sortedOCRresult = [
            (line[1][0].strip(), line[0], line[1][1])
            for result in self.result for line in result
        ] #text, bbox, confidence in self.extracted_data

    def analyze_and_extract(self):
        self._classify_document()
        self._draw_and_save_table()
        self._prepare_document_key_value_pairs()
        # for line in self.result:
        #     for word_info in line:
        #         bbox = word_info[0]  # Bounding box
        #         text = word_info[1][0].strip()  # Extracted text
        #         confidence = word_info[1][1]  # Confidence score
        #         self.sortedOCRresult.append((text, bbox, confidence))
        keyValueIdentifier = KeyValueIdentifierClass(self.sortedOCRresult,self.doc_key_list_array)
        # extracted_data = find_aligned_value(self.extracted_data, self.doc_key_list_array)
        self.keyValueData = keyValueIdentifier.getkey_extractedValues()
        save_extracted_data_remote(self.keyValueData, self.remote_path, self.doc_name)
        return self.keyValueData

    def _classify_document(self):
        classifier = documentClassifier()
        self.actual_doc_type = classifier.classify_document(self.raw_text.encode("utf-8"))
        print(f"Extracted Document and Identified as {self.actual_doc_type}")

        if self.actual_doc_type in classifier.validDocument:
            self.key_mapping_data = classifier.doc_type_mapping.get(self.actual_doc_type, self.key_mapping_data)

    def _draw_and_save_table(self):
        flattened_result = [line for result in self.result for line in result]

        drawer = OCRBoxDrawer(self.image_path, flattened_result)
        image_with_boxes = drawer.draw_boxes()

        table_detector = TableDetector(flattened_result, self.doc_name)
        image_with_table, is_table_cord = table_detector.draw_table_box(image_with_boxes)

        if is_table_cord:
            table_detector.draw_grid(image_with_table)
            table_detector.to_html()
            table_detector.to_csv()

        output_image = f"{self.doc_name}_annotated.png"
        cv2.imwrite(output_image, image_with_table)
        with open(output_image, 'rb') as f:
            image_content = f.read()
        self.sftp_uploader(image_content, output_image, self.remote_path)

    def _prepare_document_key_value_pairs(self):
        self.doc_key_list_array = getKeylist(self.result, self.key_mapping_data)
        for key in self.doc_key_list_array:
            self.doc_key_list.append(key['key'])


class KeyValueIdentifierClass:
    def __init__(self, sortedOCRresult, key_info_list, y_tolerance=20):
        self.sortedOCRresult = sortedOCRresult
        self.key_info_list = key_info_list
        self.y_tolerance = y_tolerance
        self.keys = []
        self.values = []
        self.key_value_pairs = []
        self.used_value_bboxes = []
        self.actual_bottom_threshold = 35  # Define your bottom threshold
        self.y_align4_right = 20
        self.x_align4_bottom = 35
        
    def categorize_data(self):
        print("Key info list:", self.key_info_list)
        for text, bbox, confidence in self.sortedOCRresult:
            matched = next((k for k in self.key_info_list if k["key"].lower() == text.lower()), None)
            if matched and matched["key_bounding_box"]:
                self.keys.append((matched["standard_key"], eval(matched["key_bounding_box"]), text))
            else:
                self.values.append((text, bbox))
            # Step 2: Sort by Y first, then X for better alignment detection
        self.keys.sort(key=lambda x: (x[1][0][1], x[1][0][0]))
        # Categorization of Possible Values
        self.values.sort(key=lambda x: (x[1][0][1], x[1][0][0]))

    def right_aligned(self, currentKey):
        key_bbox = json.loads(currentKey['key_bounding_box'])
        key_x1, key_y1 = key_bbox[0]  # Top-left
        key_x2, key_y2 = key_bbox[1]  # Top-right
        key_x3, key_y3 = key_bbox[2]  # Bottom-right
        key_x4, key_y4 = key_bbox[3]  # Bottom-left
        closest_value = None
        min_x_distance = float('inf')
        key_text = currentKey['standard_key']
        match_candidates = []
        
        closest_bbox = None
        for val_text, val_bbox in self.values:
            if val_bbox in self.used_value_bboxes:
                continue  # Skip reused values
            val_x1, val_y1 = val_bbox[0]
            val_x2, val_y2 = val_bbox[1]

            average = statistics.mean([key_x1, key_x2])
            if val_x1 > average and abs(val_y1 - key_y1) <= self.x_align4_bottom:
                x_distance = val_x1 - key_x2
                if x_distance < min_x_distance:
                    min_x_distance = x_distance
                    closest_value = val_text
                    closest_bbox = val_bbox
                    capturedMethod = 'right_aligned_pair'
                    closest_distance = calculate_distance(key_bbox, closest_bbox)
                    print('Right-aligned match candidate:', key_text, '-->', val_text, 'with distance', closest_distance)
                    existing_index = next((i for i, kv in enumerate(self.key_value_pairs) if kv["key"] == key_text and kv["method"] == capturedMethod), None)
                    if existing_index is not None:
                        print(f'Right-aligned match candidate at index: {existing_index} , {self.key_value_pairs[existing_index]}')
                    for threshold in range(100, 1601, 100):
                        if closest_value and closest_distance < threshold:
                            if existing_index is None:
                                self.key_value_pairs.append({
                                    "key": key_text,
                                    "value": closest_value,
                                    "key_bbox": key_bbox,
                                    "value_bbox": closest_bbox,
                                    "method": capturedMethod,
                                    "doc_text": currentKey['key'],
                                    "closest_distance": closest_distance
                                })
                                self.used_value_bboxes.append(closest_bbox)
                                print(f"[RIGHT] Matched {key_text} --> {closest_value} within threshold {threshold}: Distance = {closest_distance}")
                                break
                            else:
                                # If it exists, only replace if new distance is smaller
                                existing_entry = self.key_value_pairs[existing_index]
                                existing_distance = existing_entry.get("closest_distance", float('inf'))
                                if closest_distance < existing_distance:
                                    # Replace the existing entry
                                    self.key_value_pairs[existing_index] = {     
                                        "key": key_text,
                                        "value": closest_value,
                                        "key_bbox": key_bbox,
                                        "value_bbox": closest_bbox,
                                        "method": capturedMethod,
                                        "doc_text": currentKey['key'],
                                        "closest_distance": closest_distance
                                    }
        pass

    def bottom_aligned(self, currentKey):
        key_bbox = json.loads(currentKey['key_bounding_box'])
        key_x1, key_y1 = key_bbox[0]  # Top-left
        key_x2, key_y2 = key_bbox[1]  # Top-right
        key_x3, key_y3 = key_bbox[2]  # Bottom-right
        key_center_y = (key_y1 + key_y3) / 2
        key_right = key_x2
        bottom_closest_value = None
        min_y_distance = float('inf')
        key_text = currentKey['standard_key']
        for val_text, val_bbox in self.values:
            if val_bbox in self.used_value_bboxes:
                continue  # Skip reused values

            val_x1, val_y1 = val_bbox[0]
            val_y3 = val_bbox[2][1]
            
            # ✅ Filter values directly below key within a tight vertical margin
            y_distance = val_y1 - key_y3
            if not (0 < y_distance <= self.actual_bottom_threshold):
                continue

            # ✅ Check if it's horizontally aligned with the key
            if not (key_x1 - self.x_align4_bottom <= val_x1 <= key_x2 + self.x_align4_bottom):  # give a little buffer
                continue

            # ✅ Pick the closest y-distance only (avoid full Euclidean overshoot)
            if y_distance < min_y_distance:
                min_y_distance = y_distance
                bottom_closest_value = val_text
                closest_bbox = val_bbox
                capturedMethod = 'bottom_aligned_pair'

            if bottom_closest_value == None:
            # ✅ Value is horizontally aligned or slightly below
                if not (key_center_y - 10 <= val_y1 <= key_center_y + 20):  # allow small vertical offset
                    continue

                # ✅ Value starts to the right of the key
                if not (val_x1 >= key_right - 10):  # slight overlap allowed
                    continue

                # ✅ Use minimum horizontal distance instead of Euclidean
                x_distance = val_x1 - key_right
                if x_distance < min_y_distance:
                    min_y_distance = x_distance
                    bottom_closest_value = val_text
                    closest_bbox = val_bbox
                    capturedMethod = 'right_bottom_pair' 
            
            # ✅ Once matched loop is over, add the closest match
            if bottom_closest_value:
                closest_distance = calculate_distance(key_bbox, closest_bbox)
                self.key_value_pairs.append({
                    "key": key_text,
                    "value": bottom_closest_value,
                    "key_bbox": key_bbox,
                    "value_bbox": closest_bbox,
                    "method": capturedMethod,
                    "doc_text": currentKey['key'],
                    "closest_distance": closest_distance
                })
                print(f"✅ Bottom match for {key_text} --> {bottom_closest_value} with Y-distance: {min_y_distance}")
                self.used_value_bboxes.append(closest_bbox)
                match_found = True
        pass

    def right_bottom_aligned(self):
        # fallback alignment logic here
        pass

    def set_key_values(self, key2set):
        self.key_value_pairs.append({
            "key": key2set['standard_key'],
            "value": key2set["value"],
            "key_bbox": json.loads(key2set['key_bounding_box']),
            "value_bbox": json.loads(key2set['key_bounding_box']),
            "method": 'colon_identification',
            "doc_text": key2set['key']
        })

    def apply_regex_rules(self):
        for rule in regex_check:
            pattern = rule["pattern"]
            key_name = rule["key"]
            for text, bbox, confidence in self.sortedOCRresult:
                matches = re.findall(pattern, text)
                for match in matches:
                    self.key_value_pairs.append({
                        "key": key_name,
                        "value": match,
                        "key_bbox": bbox,
                        "value_bbox": bbox,
                        "method": "regex_match",
                        "doc_text": text
                    })

    def getkey_extractedValues(self):
        self.categorize_data()
        for eachKey in self.key_info_list:
            if eachKey["key_bounding_box"] is not None and eachKey["value"] is None:
                match_found = False
                self.right_aligned(eachKey)
                self.bottom_aligned(eachKey)
            elif eachKey["value"] is not None:
                print(f"Colon match used for: '{eachKey['standard_key']}'")    
                self.set_key_values(eachKey) #set colon Match values
        self.apply_regex_rules()
        return self.key_value_pairs



def calculate_distance(bbox1, bbox2):
    """Calculate Euclidean distance between two bounding box centers."""
    x1, y1 = (bbox1[0][0] + bbox1[2][0]) / 2, (bbox1[0][1] + bbox1[2][1]) / 2
    x2, y2 = (bbox2[0][0] + bbox2[2][0]) / 2, (bbox2[0][1] + bbox2[2][1]) / 2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)    