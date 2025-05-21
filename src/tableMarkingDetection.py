import cv2
import numpy as np
import csv
import os
import paramiko
from typing import List, Tuple
import re


class OCRBoxDrawer:
    def __init__(self, image_path: str, ocr_data: List[Tuple[List[List[int]], Tuple[str, float]]]):
        self.image_path = image_path
        self.ocr_data = ocr_data
        self.image = cv2.imread(image_path)
        self.box_color = (0, 255, 0)
        self.text_color = (255, 0, 0)
        self.thickness = 2
        self.font_scale = 0.5
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_boxes(self):
        for points, (text, conf) in self.ocr_data:
            points = np.array(points, dtype=np.int32)
            cv2.polylines(self.image, [points], isClosed=True, color=self.box_color, thickness=self.thickness)
            # x, y = points[0]
            # cv2.putText(self.image, text, (x, y - 10), self.font, self.font_scale, self.text_color, 1, cv2.LINE_AA)
        return self.image

    def save_image(self, output_path: str):
        cv2.imwrite(output_path, self.image)
        return output_path


class TableDetector:

    def __init__(self, ocr_data: List[Tuple[List[List[int]], Tuple[str, float]]], doc_name, doc_text_lables,documentMasterInfo,actual_doc_type):
        self.ocr_data = ocr_data
        self.actual_doc_type = actual_doc_type
        self.documentMasterInfo = documentMasterInfo
        # self.start_keywords = ['Particulars','Package','item', 'CATEGORY','(Rs.)','description', 'qty', 'quantity', 'rate', 'amount', 'hsn', 'price', 
        #                        'net charges','discount','CGST','Amt','Amount','SGST','(Rate)', 'Taxable', 'Cess','Candidates',
        #                         'sr', 'no.', 'tax', 'items', 'purchased', 'value']
        # self.end_keywords = ['Tax Summary','Sub Total','Round Off','Total','Total value', 'grand total', 'invoice total','Totals', 'amount in words','Gross Amount/Total',
        #                      'Taxable Amount','Gross Amount', 'RUPEES IN WORDS:','Amount Chargeable','Current Total', 'Item Total']
        # self.wrapKeys= ['Product Description','Item & Description','Description Of Services','Description Of Goods (Mfg Mkt)','Description of','SI Description of Goods No.',
        #                 'Description/ ISN/UOM City','Description of Service','ITEM(S) PURCHASED','Desc of Goods','Item Description','Item Details','Service Description','Month',
        #                 'HSN Code and Description','Name of the Product','ITEM NAME','Description','Particulars','ITEM','SI Description of Goods No','Froduct Nane','Package','Description of Goods']
        self.exclude_list = ['9%', '18%']
        self.start_keywords = self.documentMasterInfo['table_start_position']['fieldKeys'] if self.documentMasterInfo else []
        self.end_keywords = self.documentMasterInfo['table_end_position']['fieldKeys'] if self.documentMasterInfo else []
        self.wrapKeys = self.documentMasterInfo['Description']['fieldKeys'] if self.documentMasterInfo else []
        self.file_name = doc_name
        self.table_start_y = self.detect_table_start()
        self.table_end_y = self.detect_table_end()
        self.doc_text_lables = doc_text_lables
        self.table_region = self.get_table_region()
        # Filter only elements within the table region
        self.table_elements = [
            item for item in self.ocr_data
            if (self.table_start_y is not None and min(p[1] for p in item[0]) >= self.table_start_y-5) and
               (self.table_end_y is None or max(p[1] for p in item[0]) <= self.table_end_y)
        ]

        self.rows = self.identify_rows(self.table_elements)
        self.mergedRows = []
        # self.mergedRows = self.merge_wrapped_text_rows(self.table_elements)
        self.columns = self.identify_merged_columns(self.rows) if self.actual_doc_type =='INVOICE' else self.identify_columns(self.rows)
        self.table_cord = ''
        self.table_data = []
        self.table_header_info = []
        self.table_noise_rows = []
        
    def detect_table_start(self):
        sorted_data = sorted(self.ocr_data, key=lambda item: min(p[1] for p in item[0]))
        # print('Sorted OCR Data ---->  ', sorted_data )
        for polygon, (text, conf) in sorted_data:
            lower_text = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', text.lower().strip())
            if lower_text !='' and lower_text != None and  any(kw.lower().strip() == lower_text for kw in self.start_keywords):
                y_start = min(p[1] for p in polygon)
                print(f'Table start detected  - at - {y_start} with Matched Keyword {lower_text}')
                return y_start
        return None

    def detect_table_end(self):
        if self.table_start_y is None:
            return None
        normalized_keywords = [re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', kw.lower().strip()) for kw in self.end_keywords]
        matched_positions = []

        print("🔍 Matching OCR items against end keywords...\n")

        for polygon, (text, conf) in self.ocr_data:
            if not text or not polygon:
                continue
            lower_text = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', text.lower().strip())
            if any(kw == lower_text for kw in normalized_keywords):
                top_y = max(p[1] for p in polygon)
                if(self.table_start_y != None and top_y > self.table_start_y+100):
                    matched_positions.append((top_y, text))
                    print(f"✅ Match found: '{text}' at top Y: {top_y}")
            elif re.search(r'(?i)rupees\s+.+?\s+only', text):
                top_y = max(p[1] for p in polygon)
                if(self.table_start_y != None and top_y > self.table_start_y+100):
                    matched_positions.append((top_y, text))
                    print(f"✅ Match found with Rupee Pattern: '{text}' at top Y: {top_y}")
                # break  # avoid duplicate matching for multiple keywords in one text

        if matched_positions:
            y_end, matched_text = min(matched_positions, key=lambda x: x[0])
            print(f"\n🏁 Final y_end selected: {y_end} from matched text: '{matched_text}'")
            return y_end
        else:
            print("❌ No matching end keyword found.")
            return None

    def get_table_region(self):
        if self.table_start_y is None:
            return (0, 0, 0, 0)

        # Filter lines between start and end Y
        table_boxes = [
            np.array(polygon, dtype=np.int32)
            for polygon, _ in self.ocr_data
            if min(p[1] for p in polygon) >= self.table_start_y and
               (self.table_end_y is None or max(p[1] for p in polygon) <= self.table_end_y)
        ]

        if not table_boxes:
            return (0, 0, 0, 0)

        all_points = np.vstack(table_boxes)
        x, y, w, h = cv2.boundingRect(all_points)
        self.table_cord = cv2.boundingRect(all_points)
        return (x, y, x + w, y + h)

    def draw_table_box(self, image):
        is_table_detected=''
        x1, y1, x2, y2 = self.get_table_region()
        print('Table region detected from the method ->', self.get_table_region() )
        if x1 == x2 and y1 == y2:
            print("[INFO] Table region not detected.")
            is_table_detected = False
        else:
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            is_table_detected = True
        return image, is_table_detected

    # common issue in OCR-based row detection: wrapped (multi-line) headers can confuse row detection logic because they span more vertical 
    # space than single-line headers, and the Y-position comparison logic assumes uniform height.
    def identify_rows(self, table_elements, row_threshold=10):
        sorted_data = sorted(table_elements, key=lambda item: item[0][0][1])
        rows = []
        current_row = []
        last_y = None
        for polygon, text_info in sorted_data:
            y_top = polygon[0][1]
            if last_y is None or abs(y_top - last_y) <= row_threshold:
                current_row.append((polygon, text_info))
            else:
                rows.append(current_row)
                current_row = [(polygon, text_info)]
            last_y = y_top
        if current_row:
            rows.append(current_row)
        
        headerRow= []
        for eachRow in rows[:5]:
            row_matched = self.is_headertext(eachRow)
            if row_matched:
                headerRow.append(eachRow)
        
        # Merge the extracted rows
        print('--------------------------------')
        print(headerRow)
        print('--------------------------------')
        merged_row = self.identify_Merged_rows(headerRow)
        
        # Remove the extracted rows from the original list
        if len(merged_row) >0 :
            for row in headerRow:
                rows.remove(row)
            rows.insert(0, merged_row)
        print('Returned Rows ------------>' ,rows )
        return rows
    
    def identify_Merged_rows(self, ocr_data):
        # Step 1: Group cells by approximate column (based on x-coordinates)
        def get_avg_x(bbox):
            return (bbox[0][0] + bbox[1][0] + bbox[2][0] + bbox[3][0]) / 4

        # Collect all cells with their row index and calculate their average x-coordinate
        cells = []
        for row_idx, row in enumerate(ocr_data):
            for cell in row:
                bbox, (text, conf) = cell
                avg_x = get_avg_x(bbox)
                cells.append((avg_x, bbox, text, conf, row_idx))

        # Sort cells by avg_x to group by columns
        cells.sort(key=lambda x: x[0])

        # Group cells into columns based on x-coordinate proximity
        columns = []
        current_column = []
        last_x = None
        x_threshold = 50  # Adjusted to separate cells appropriately

        for cell in cells:
            avg_x, bbox, text, conf, row_idx = cell
            if last_x is None or abs(avg_x - last_x) < x_threshold:
                current_column.append((bbox, text, conf, row_idx))
            else:
                columns.append(current_column)
                current_column = [(bbox, text, conf, row_idx)]
            last_x = avg_x

        if current_column:
            columns.append(current_column)

        # Step 2: Merge cells within each column
        merged_row = []
        for column in columns:
            if not column:
                continue
            
            # Sort by y-coordinate (top-left y) to maintain top-to-bottom order
            column.sort(key=lambda x: x[0][0][1])
            
            # Merge text
            merged_text = " ".join(cell[1] for cell in column)
            
            # Take confidence from the first cell (based on y-order)
            merged_conf = column[0][2]
            
            # Merge bounding boxes
            bboxes = [cell[0] for cell in column]
            min_x1 = min(bbox[0][0] for bbox in bboxes)  # min x1
            min_y1 = min(bbox[0][1] for bbox in bboxes)  # min y1
            max_x2 = max(bbox[1][0] for bbox in bboxes)  # max x2
            min_y2 = min(bbox[1][1] for bbox in bboxes)  # min y2
            max_x3 = max(bbox[2][0] for bbox in bboxes)  # max x3
            max_y3 = max(bbox[2][1] for bbox in bboxes)  # max y3
            min_x4 = min(bbox[3][0] for bbox in bboxes)  # min x4
            max_y4 = max(bbox[3][1] for bbox in bboxes)  # max y4
            
            merged_bbox = [
                [min_x1, min_y1],
                [max_x2, min_y2],
                [max_x3, max_y3],
                [min_x4, max_y4]
            ]
            
            merged_row.append((merged_bbox, (merged_text, merged_conf)))

        # Step 3: Sort merged_row by min_x1 to maintain left-to-right order
        merged_row.sort(key=lambda x: x[0][0][0])
        
        return merged_row
    
    def identify_columns(self, rows, col_threshold=3, row_limit=3):
        if not rows:
            return []
        new_column_positions = []      
        # Step 1: Analyze first N rows (or all rows)
        headerRow = rows[0]
        print('Identify the Header rows as in identify_columns ######################' , headerRow)
        for ridx , (polygon, (text, conf)) in enumerate(headerRow):
            if text.lower() in [key.lower() for key in self.wrapKeys]:
                if ridx > 0:
                    print(f'Desc Matched and altered to --->{headerRow[ridx-1]} ')
                    prvPoly, text = headerRow[ridx-1]
                    x_left = max([pt[0] for pt in prvPoly])
                    new_column_positions[-1] = (new_column_positions[-1][0], x_left)
                elif ridx == 0:
                    print(f'Desc Matched and altered to Table start left--->{self.get_table_region()[0]} ')
                    x_left = self.get_table_region()[0]
            else:
                x_left = min([pt[0]-30 for pt in polygon])
                print(f'If Desc not matched ---> {x_left}  and its text {text} and index ridx {ridx}')
                
            if ridx < len(headerRow)-1:
                print(f'Identifying the Header row at position {ridx+1} and the current row value {headerRow[ridx+1]}')
                nextPolyon, text = headerRow[ridx+1]    
                x_right = min([pt[0] for pt in nextPolyon])              
            else:
                x_right = max([pt[0] for pt in polygon])
            new_column_positions.append((x_left, x_right))
        new_column_positions[-1] = (new_column_positions[-1][0], self.get_table_region()[2])
        
        print('🏁 Modified new_column_positions  ------> ', new_column_positions)
        return new_column_positions

    def identify_merged_columns(self, rows, col_threshold=3, row_limit=3):
        if not rows:
            return []
        column_positions = []
        # Step 1: Analyze first N rows (or all rows)
        headerRow = rows[0]
        print('Identify the Header rows as in identify_merged_columns ######################' , headerRow)      
        i = 0
        while i < row_limit and i < len(rows):
            row = rows[i]
            print(f'🏁 Row {i + 1}/{row_limit} Identified ---> Length: {len(row)}, Header: {row}')
            
            if len(row) >= len(headerRow) / 2:
                for polygon, text in row:
                    x_left = min(pt[0] for pt in polygon)
                    x_right = max(pt[0] for pt in polygon)
                    column_positions.append((x_left, x_right))
            else:
                print(f"⚠️ Row {i + 1} too short; increasing row_limit from {row_limit} to {row_limit + 1}")
                row_limit += 1  # Extend row_limit to consider more rows
            i += 1
        
        # for row in rows[:row_limit]:
        #     print(f'🏁 Row {idx + 1}/{row_limit} Identified ---> Length: {len(row)}, Header: {row}')
        #     if len(row) >= len(headerRow)/2 :
        #         for polygon, text in row:
        #             x_left = min([pt[0] for pt in polygon])
        #             x_right = max([pt[0] for pt in polygon])
        #             column_positions.append((x_left, x_right))
        #     else: row_limit = 1+row_limit

        # Step 2: Sort left positions
        column_positions.sort(key=lambda x: x[0])
        # Step 3: Merge overlapping/close columns
        merged_columns = []

        for col in column_positions:
            if not merged_columns:
                merged_columns.append(col)
            else:
                last = merged_columns[-1]
                # print(f'this is in the col check col[0]{col[0]} and the last {last[1]} ')
                if col[0] - last[1] <= col_threshold:
                    merged_columns[-1] = (min(last[0], col[0]), max(last[1], col[1]))
                else:
                    merged_columns.append(col)
        print('🏁 Modified merged_columns positions ------> ', merged_columns)
        if len(headerRow) != len(merged_columns):
            print('Header Didnt matched with merged Column, Switching to New Col position')
            merged_columns = self.identify_columns(self.rows)
        return merged_columns

    def find_wrap_keys_in_headers(self,header_rows):
        """
        Check if any wrap_keys are present in header_rows and return their positions.
        
        Args:
            header_rows (list): List of header names.
            wrap_keys (list): List of keys to search for in header_rows.
        
        Returns:
            list: List of tuples (key, index, header) for matching keys and their positions.
        """
        matches = []
        print('Header Row ---------------> ', header_rows)
        # Convert header_rows to lowercase for case-insensitive comparison
        header_rows_lower = [header.lower().strip() for header in header_rows]
        
        # Check each wrap key
        for key in self.wrapKeys:
            # Convert key to lowercase for comparison
            key_lower = key.lower().strip()
            
            # Check if the key is in any header (partial or full match)
            for idx, header in enumerate(header_rows_lower):
                if key_lower in header:
                    matches.append((key, idx, header_rows[idx]))  # Store original key, index, and original header
        return matches
    
    def is_headertext(self, rowItem):
        start_keywords_set = set(kw.strip().lower() for kw in self.start_keywords)
        matched_count = 0
        total_items = len(rowItem)
        # print("Exact Match Results:")
        # print("---------------------")
        for rcnt, (_, (text, _)) in enumerate(rowItem):
        # for rcnt, (val) in enumerate(rowItem):
            cleaned_text = text.strip().lower()
            if cleaned_text in start_keywords_set:
                matched_count += 1

        # Compute Match Score
        match_score = matched_count / total_items if total_items > 0 else 0
        print("\nHeader match count Total Matches:", matched_count)
        # print("Match Score:", f"{match_score:.2f}")
        if matched_count >=1:
            return True
        else: 
            return False
    
    def identify_as_headerRow(self, rowItem):
        start_keywords_set = set(kw.strip().lower() for kw in self.start_keywords)
        matched_count = 0
        total_items = len(rowItem)
        # print("Exact Match Results:")
        # print("---------------------")
        # for rcnt, (_, (text, _)) in enumerate(rowItem):
        for rcnt, (val) in enumerate(rowItem):
            cleaned_text = val.strip().lower()
            if cleaned_text in start_keywords_set:
                matched_count += 1

        # Compute Match Score
        match_score = matched_count / total_items if total_items > 0 else 0
        print("\nTotal Matches:", matched_count, ' for rowItem, ', rowItem)
        # print("Match Score:", f"{match_score:.2f}")
        if matched_count >=1:
            return True
        else: 
            return False

    def get_table_info(self):
        header_row = self.rows[0]  # Take the first row as the header
        sortedCol = sorted(self.columns, key=lambda x: x[0])
        sortedRows = []
        filtered_labels = [
            kw.lower().strip()
            for kw in self.doc_text_lables
            if kw.strip() not in self.exclude_list
        ]
        # print('Inside get_table_info Rows ------------>' ,self.rows )
        # print('Inside get table Columns---------->', self.columns)
        # Find matches
        matchedIndex = []
        print('Last row Identification logic build -> ', self.table_end_y)
        for ridx, eachRow in enumerate(self.rows):
            # print(f'Processing rows and Cols {ridx} and its row details {eachRow}')
            # if len(self.rows)-1 == ridx:
            #     continue # To Skip the last row item from the Detected Table element
            rowItem = True
            isLinexclude = False
            eachRow = sorted(eachRow, key=lambda x: x[0][0][0])
            # print('post Sorted row ', eachRow)
            sortedRows.append(eachRow)
            row_data = ['null'] * len(sortedCol)
            for box, (text, conf) in eachRow:
                x_min = min([pt[0] for pt in box])
                x_max = max([pt[0] for pt in box])
                x_center = (x_min + x_max) / 2
                # if text.lower() in [kw.lower().strip() for kw in ['CGST @ 9%','SGST @ 9%','Total']]:
                # Filter or Clean Extract rows 
                if text.lower().strip() in filtered_labels:
                    rowItem = False
                for idx, (col_start, col_end) in enumerate(sortedCol):
                    # print(f'Identifying cell match for {text} and its center {x_center} and col position {col_start} - {col_end}')
                    if col_start <= x_center <= col_end-15:
                        row_data[idx] = text
                        # print('row_data pushed ', row_data)
                        break
                non_null_count = sum(1 for item in row_data if item != 'null')
            # print('Processed row info ' , row_data)
            if ridx == 0:
                matches = self.find_wrap_keys_in_headers(row_data)
                # Print results
                if matches:
                    print("Matches found:")
                    for key, idx, header in matches:
                        print(f"Key: '{key}' found in header: '{header}' at index: {idx}")
                        matchedIndex.append(idx)
                else:
                    print("No wrap_keys found in header_rows.")
                                       
            is_Header_row = self.identify_as_headerRow(row_data)
            print(f'Table detection values in sorted ----> {row_data} and rowItem matched - {rowItem}  and Header Identifiction as {is_Header_row} for Index row {ridx} and non_null_count is {non_null_count}' )
            if non_null_count <= 2 and len(self.table_data) > 0 and rowItem:
                print('Identified as Table row and for Row  ', rowItem)
                lastRowItemIdx = len(self.table_data)-1
                is_LastItem_Header_row = self.identify_as_headerRow(self.table_data[lastRowItemIdx])
                print(f' table row data for last index {is_LastItem_Header_row} and data is {self.table_data[-1]}')
                if is_LastItem_Header_row == False:
                    for eidx, eachCell in enumerate(row_data):
                        # if eachCell != 'null' and eidx <= len(row_data)/2:
                        #     self.table_data[lastRowItemIdx][eidx] = self.table_data[lastRowItemIdx][eidx] + ' ' + eachCell
                        print('Inside Identified as Table row and for Row  ', row_data)
                        if eachCell != 'null' and eidx <= len(row_data)/2 and eidx in matchedIndex:
                            print('Merging Rows Identified as Table row and for Row  ', rowItem)
                            self.table_data[lastRowItemIdx][eidx] = self.table_data[lastRowItemIdx][eidx] + ' ' + eachCell
                            isLinexclude = False
                        else: isLinexclude = True
                        
                    if isLinexclude:  self.table_noise_rows.append(row_data)
                    continue
                else:
                    self.table_data.append(row_data)
            elif rowItem or ridx == 0:
                print('Inside Else Identified as Table row and for Row  ', row_data)
                self.table_data.append(row_data)
            else: 
                self.table_noise_rows.append(row_data)
        print("---------------------")
        print('Sorted Rows Table Header Info ---------> ', self.table_data )
        
        print('Noise Information ---------> ', self.table_noise_rows )
        for i, (cell, (key, confidence)) in enumerate(sortedRows[0]):
            if i < len(sortedCol):
                col_start, col_end = sortedCol[i]
                self.table_header_info.append({
                    "key": key.strip(),
                    "position": i + 1,
                    "coordinates": (col_start, col_end)
                })
        print('Table Header Info ---------> ',self.table_header_info )
        # return table_header_info

    def map_and_get_tableData(self, image):
        rows = self.rows
        columns = self.columns
        # print('Columns to Print ------> ', columns)
        # print(f'row start position begin {int(columns[0][0])} and end at {int(columns[-1][1])}')
        x,y,w,h = self.table_cord
        for row in rows:
            y_coords = [polygon[0][1] for polygon, _ in row]
            if y_coords:
                y = int(np.mean(y_coords))
                # cv2.line(image, (int(columns[0][0]), y), (int(columns[-1][1]), y), (255, 0, 0), 3)
                cv2.line(image, (x, y), (x+w, y), (255, 0, 0), 3)

        for col in columns:
            x1, x2 = map(int, col)
            y_top = int(rows[0][0][0][0][1])
            y_bottom = int(rows[-1][0][0][0][1])
            cv2.line(image, (x1, y_top), (x1, y_bottom), (255, 0, 0), 3)
        self.get_table_info()
        return image
    
    def to_html(self):
        output_file=f"{self.file_name}_output_table.html"
        html = "<html><body><table border='1'>\n"
        for row in self.rows:
            html += "<tr>"
            for cell, value in row:
                # Handle both raw text or (text, confidence)
                if isinstance(value, tuple):
                    text = value[0]
                else:
                    text = value
                html += f"<td>{text.strip()}</td>"
            html += "</tr>\n"
        html += "</table></body></html>"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        return output_file

    def to_csv(self):
        output_file= f"{self.file_name}_output_table.csv"
        with open(output_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in self.rows:
                processed_row = []
                for _, value in row:
                    text = value[0] if isinstance(value, tuple) else value
                    processed_row.append(text.strip())
                writer.writerow(processed_row)
        return output_file
    
    # def extract_table_data(self, table_cells: List[Dict], headers: List[str], header_coords: List[Tuple[int, int]]) -> List[List[str]]:
    #     """
    #     Extracts structured table data from OCR cell info and given headers.
        
    #     Args:
    #         table_cells: List of cell dicts with keys: ['text', 'bbox'].
    #         headers: The ordered list of header names.
    #         header_coords: List of x-coordinate range (start_x, end_x) for each column header.
        
    #     Returns:
    #         List of lists: structured rows including headers and corresponding row values.
    #     """
    #     table_data = [headers]
    #     rows_by_y = {}

    #     # Step 1: Group cells by Y-coordinate (rows)
    #     for cell in table_cells:
    #         x_min, y_min, x_max, y_max = cell['bbox']
    #         text = cell['text'].strip()
    #         row_key = (y_min + y_max) // 2  # approximate row center

    #         if row_key not in rows_by_y:
    #             rows_by_y[row_key] = []

    #         rows_by_y[row_key].append({
    #             "text": text,
    #             "x_center": (x_min + x_max) // 2
    #         })

    #     # Step 2: Sort rows by their vertical position (top to bottom)
    #     sorted_row_keys = sorted(rows_by_y.keys())
    #     for row_key in sorted_row_keys:
    #         row = rows_by_y[row_key]
    #         row_cells = [""] * len(headers)

    #         # Step 3: Match each cell to the correct column based on x_center
    #         for cell in row:
    #             x = cell["x_center"]
    #             text = cell["text"]
    #             for i, (x_start, x_end) in enumerate(header_coords):
    #                 if x_start <= x <= x_end:
    #                     row_cells[i] = text
    #                     break

    #         # Check if at least one column is non-empty before appending
    #         if any(val != "" for val in row_cells):
    #             table_data.append(row_cells)

    #     return table_data

    
    
    
    
    
    # def draw_table_cell(self, image, rows, columns):
    #     for row in rows:
    #         y_coords = [pt[0][1] for pt, _ in row]
    #         height = max([max(pt[1] for pt in polygon) for polygon, _ in row]) - min([min(pt[1] for pt in polygon) for polygon, _ in row])
    #         y = int(np.mean(y_coords))

    #         for col in columns:
    #             x1, x2 = col
    #             top_left = (x1, y)
    #             bottom_right = (x2, y + height)
    #             cv2.rectangle(image, top_left, bottom_right, (0, 255, 255), 1)  # Yellow cells

    #     return image

class SFTPUploader:
    def __init__(self, host, port, username, password, sftp_folder):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sftp_folder = sftp_folder

    def upload_file(self, local_path: str, remote_filename: str):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        sftp.chdir(self.sftp_folder)
        sftp.put(local_path, remote_filename)

        sftp.close()
        transport.close()
        print(f"Uploaded {local_path} to SFTP as {remote_filename}")
