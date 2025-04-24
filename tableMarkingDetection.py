import cv2
import numpy as np
import csv
import os
import paramiko
from typing import List, Tuple


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

    def __init__(self, ocr_data: List[Tuple[List[List[int]], Tuple[str, float]]], doc_name):
        self.ocr_data = ocr_data
        self.keywords = ['Particulars','Package','item', 'description', 'qty', 'quantity', 'rate', 'amount', 'hsn', 'price', 'net charges','discount','CGST','SGST','']
        self.end_keywords = ['Round Off','Total', 'grand total', 'invoice total','Totals', 'amount in words','Gross Amount/Total','Taxable Amount','Gross Amount', 'RUPEES IN WORDS:','Amount Chargeable','Current Total']
        self.file_name = doc_name
        self.table_start_y = self.detect_table_start()
        self.table_end_y = self.detect_table_end()
        # self.columns = self.identify_columns()
        # self.rows = self.identify_rows()

            # Filter only elements within the table region
        self.table_elements = [
            item for item in self.ocr_data
            if (self.table_start_y is not None and min(p[1] for p in item[0]) >= self.table_start_y-5) and
               (self.table_end_y is None or max(p[1] for p in item[0]) <= self.table_end_y)
        ]

        self.rows = self.identify_rows(self.table_elements)
        self.columns = self.identify_columns(self.rows)
        self.table_cord = ''
        
    def detect_table_start(self):
        sorted_data = sorted(self.ocr_data, key=lambda item: min(p[1] for p in item[0]))
        # print('Sorted OCR Data ---->  ', sorted_data )
        for polygon, (text, conf) in sorted_data:
            lower_text = text.lower()
            if any(kw == lower_text for kw in self.keywords):
                y_start = min(p[1] for p in polygon)
                print('Table start detected  - at - ',y_start)
                return y_start
        return None

    def detect_table_end_old(self):
        sorted_data = sorted(self.ocr_data, key=lambda item: min(p[1] for p in item[0]))
        for polygon, (text, conf) in reversed(sorted_data):  # Start from bottom
            lower_text = text.lower().strip()
            if lower_text in [kw.lower() for kw in self.end_keywords]:
                y_end = max(p[1] for p in polygon)
                return y_end
        return None
    
    def detect_table_end(self):
        normalized_keywords = [kw.lower().strip() for kw in self.end_keywords]
        matched_positions = []

        print("🔍 Matching OCR items against end keywords...\n")

        for polygon, (text, conf) in self.ocr_data:
            if not text or not polygon:
                continue
            lower_text = text.lower().strip()
            if any(kw == lower_text for kw in normalized_keywords):
                top_y = max(p[1] for p in polygon)
                if(top_y > self.table_start_y+50):
                    matched_positions.append((top_y, text))
                    print(f"✅ Match found: '{text}' at top Y: {top_y}")
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
        print('Table region detected from the method ->', x1, y1, x2, y2 )
        if x1 == x2 and y1 == y2:
            print("[INFO] Table region not detected.")
            is_table_detected = False
        else:
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            is_table_detected = True
        return image, is_table_detected

    # common issue in OCR-based row detection: wrapped (multi-line) headers can confuse row detection logic because they span more vertical space than single-line headers, and the Y-position comparison logic assumes uniform height.
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
        return rows
    
    def identify_rows_v1(self, table_elements, row_threshold=10):
        # Sort based on the top of each element
        sorted_data = sorted(table_elements, key=lambda item: min(p[1] for p in item[0]))
        
        rows = []
        current_row = []
        current_min_y, current_max_y = None, None

        for polygon, text_info in sorted_data:
            poly_ys = [p[1] for p in polygon]
            min_y, max_y = min(poly_ys), max(poly_ys)

            if not current_row:
                current_row.append((polygon, text_info))
                current_min_y, current_max_y = min_y, max_y
                continue

            # Check if the current element vertically overlaps with the previous row
            overlaps = not (max_y < current_min_y - row_threshold or min_y > current_max_y + row_threshold)

            if overlaps:
                current_row.append((polygon, text_info))
                current_min_y = min(current_min_y, min_y)
                current_max_y = max(current_max_y, max_y)
            else:
                rows.append(current_row)
                current_row = [(polygon, text_info)]
                current_min_y, current_max_y = min_y, max_y

        if current_row:
            rows.append(current_row)

        return rows

    def identify_columns(self, rows, col_threshold=5, row_limit=3):
        if not rows:
            return []

        column_positions = []
        print('Inside table ---> ', rows)
        # Step 1: Analyze first N rows (or all rows)
        for row in rows[:row_limit]:
            for polygon, text in row:
                x_left = min([pt[0] for pt in polygon])
                x_right = max([pt[0] for pt in polygon])
                column_positions.append((x_left, x_right))

        # Step 2: Sort left positions
        column_positions.sort(key=lambda x: x[0])
        print('🏁 Identified Columns positions ------> ', column_positions)
        # Step 3: Merge overlapping/close columns
        merged_columns = []
        for col in column_positions:
            if not merged_columns:
                merged_columns.append(col)
            else:
                last = merged_columns[-1]
                print(f'this is in the col check col[0]{col[0]} and the last {last[1]} ')
                if col[0] - last[1] <= col_threshold:
                    merged_columns[-1] = (min(last[0], col[0]), max(last[1], col[1]))
                else:
                    merged_columns.append(col)
        print('Final merged columns after detection -----------> ', merged_columns)
        return merged_columns

    def identify_columns_old(self, rows, col_threshold=10):
        if not rows:
            return []

        first_row = rows[0]
        sorted_row = sorted(first_row, key=lambda item: item[0][0][0])
        
        columns = []
        for polygon, _ in sorted_row:
            x_left = min([point[0] for point in polygon])
            x_right = max([point[0] for point in polygon])
            columns.append((x_left, x_right))

        merged_columns = []
        for col in sorted(columns, key=lambda c: c[0]):
            if not merged_columns:
                merged_columns.append(col)
            else:
                last = merged_columns[-1]
                if col[0] - last[1] <= col_threshold:
                    merged_columns[-1] = (last[0], max(last[1], col[1]))
                else:
                    merged_columns.append(col)

        return merged_columns

    def identify_columns_v1(self, rows, col_threshold=15):
        if not rows:
            return []

        column_positions = []

        # Step 1: Collect x1-x2 positions of all items in all rows
        for row in rows:
            print('Rows before Polygon Detection  -------->...........' , rows)
            for polygon, _ in row:
                print('Row Polygon to print       -------->...........' , polygon)
                x_left = min([point[0] for point in polygon])
                x_right = max([point[0] for point in polygon])
                column_positions.append((x_left, x_right))

        # Step 2: Sort by left x position
        column_positions.sort(key=lambda x: x[0])

        # Step 3: Merge close columns
        merged_columns = []
        for col in column_positions:
            if not merged_columns:
                merged_columns.append(col)
            else:
                last = merged_columns[-1]
                if col[0] - last[1] <= col_threshold:
                    # Merge columns
                    new_col = (min(last[0], col[0]), max(last[1], col[1]))
                    merged_columns[-1] = new_col
                else:
                    merged_columns.append(col)

        return merged_columns

    def draw_grid(self, image):
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
            print(f'columns start position begin {y_top} and end at {y_bottom}')
            cv2.line(image, (x1, y_top), (x1, y_bottom), (255, 0, 0), 3)

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
