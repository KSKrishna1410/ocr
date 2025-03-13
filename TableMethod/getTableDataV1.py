from paddleocr import PaddleOCR
import numpy as np
from tabulate import tabulate
from collections import defaultdict 
# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang="en")  

# Perform OCR on the image
# output_folder = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\docs\images"  # Folder to save PNGs
img_path = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\inputs\13.05.2024__digital_track-1.png"
result = ocr.ocr(img_path, cls=True)

# # Read OCR output from file
# ocr_file_path = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\inputs\13.05.2024__digital_track-1_paddleocr_result.json"

# with open(ocr_file_path, "r", encoding="utf-8") as f:
#     result = f.readlines()  # Read all lines from the file

# # Process the OCR result (cleaning, splitting, etc., if necessary)
# result = [line.strip() for line in result if line.strip()]  # Remove empty lines

# Function to group text into tables based on bounding boxes
def extract_tables_old(ocr_result):
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
                "text": text[0] if isinstance(text, list) else text,  # Extract text
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_max,
                "y_max": y_max
            })
        
        # Sort words top-to-bottom by y_min
        words.sort(key=lambda word: word["y_min"])

        table = []
        current_row = []
        prev_y = None
        row_threshold = 10  # Adjust this threshold based on spacing

        for word in words:
            if prev_y is not None and abs(word["y_min"] - prev_y) > row_threshold:
                # Sort row by x_min before adding
                table.append(sorted(current_row, key=lambda w: w["x_min"]))
                current_row = []

            current_row.append(word)
            prev_y = word["y_min"]

        if current_row:
            table.append(sorted(current_row, key=lambda w: w["x_min"]))

        # Extract just the text for tabulation
        formatted_table = [[cell["text"] for cell in row] for row in table]
        table_data.append(formatted_table)

    return table_data

def format_table(tables):
    formatted_tables = []
    
    for table in tables:
        if not table:
            continue

        # Determine column widths
        num_columns = max(len(row) for row in table)
        col_widths = [max(len(row[i]) if i < len(row) else 0 for row in table) for i in range(num_columns)]

        # Create table structure
        horizontal_line = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"

        formatted_table = [horizontal_line]

        for row in table:
            row_cells = [row[i] if i < len(row) else "" for i in range(num_columns)]
            formatted_row = "| " + " | ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row_cells)) + " |"
            formatted_table.append(formatted_row)
            formatted_table.append(horizontal_line)

        formatted_tables.append("\n".join(formatted_table))

    return "\n\n".join(formatted_tables)

def extract_and_format_table(ocr_result):
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
        
        # Sort words by vertical position
        words.sort(key=lambda word: word["y_min"])

        # Group words into rows based on y_min values
        row_threshold = 10  # Vertical threshold to detect new rows
        rows = defaultdict(list)
        row_index = 0
        prev_y = None

        for word in words:
            if prev_y is not None and abs(word["y_min"] - prev_y) > row_threshold:
                row_index += 1  # Move to next row
            
            rows[row_index].append(word)
            prev_y = word["y_min"]

        # Sort words within each row by x_min
        structured_rows = [
            [w["text"] for w in sorted(row, key=lambda w: w["x_min"])]
            for row in rows.values()
        ]

        table_data.append(structured_rows)

    return format_table(table_data)

def identify_tables(ocr_output):
    """
    Identifies tables within OCR output and extracts their structure and content.

    Args:
        ocr_output: A list of lists containing OCR detection results.

    Returns:
        A list of dictionaries, where each dictionary represents a table and contains:
            - "rows": A list of lists, where each inner list represents a row and
              contains the text content of each cell in that row.
    """

    tables = []
    current_table = []
    row_threshold = 20  # Adjust this value based on the typical height of a row
    column_threshold = 50 # Adjust this value based on typical column width

    def is_within_row(element, row, row_threshold):
        """Check if an element belongs to a given row."""
        if not row:
            return True
        last_element = row[-1]
        y1_element = element[0][0][1]
        y2_element = element[0][2][1]
        y1_last = last_element[0][0][1]
        y2_last = last_element[0][2][1]

        # Check for overlap in the vertical dimension
        return max(y1_element, y1_last) - min(y2_element, y2_last) < row_threshold

    def is_within_column(element, last_element, column_threshold):
        """Check if an element belongs to the same column as the previous element."""
        x1_element = element[0][0][0]
        x2_element = element[0][2][0]
        x1_last = last_element[0][0][0]
        x2_last = last_element[0][2][0]

        # Check if the horizontal distance between elements is small enough
        return abs(x1_element - x2_last) < column_threshold or abs(x1_last - x2_element) < column_threshold

    def finalize_table(current_table):
        """Convert the raw table data into a structured format."""
        table_data = {"rows": []}
        for row in current_table:
            cells = []
            last_element = None
            current_cell = []
            for element in row:
                if last_element is None or is_within_column(element, last_element, column_threshold):
                    current_cell.append(element[1][0])
                else:
                    cells.append(" ".join(current_cell))
                    current_cell = [element[1][0]]
                last_element = element
            if current_cell:
                cells.append(" ".join(current_cell))
            table_data["rows"].append(cells)
        return table_data

    for element_group in ocr_output:
        for element in element_group:
            if not current_table:
                current_table.append([element])
            else:
                last_row = current_table[-1]
                if is_within_row(element, last_row, row_threshold):
                    last_row.append(element)
                else:
                    current_table.append([element])

    if current_table:
        table_data = finalize_table(current_table)
        tables.append(table_data)

    return tables

# Print extracted table data in tabular format
print(result)
newTableMethod = identify_tables(result)
print('newTableMethod -------->', newTableMethod)

# tables = extract_and_format_table(result)
# for table_index, table in enumerate(tables):
#     print(f"\nTable {table_index + 1}:")
#     print(tabulate(table, headers="firstrow", tablefmt="grid"))  # Neatly formatted table