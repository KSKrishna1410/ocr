from paddleocr import PaddleOCR

# Corrected image path (provide full file name with extension)
image_path = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\tabula_bank_stmt\cleaned_data\idfc_first_bank-1.png"

# Initialize OCR
# ocr = PaddleOCR(use_angle_cls=True, lang='en')
ocr = PaddleOCR(use_angle_cls=True, lang='en', rec_algorithm='CRNN', det_db_box_thresh=0.5)
# Extract text and bounding boxes
result = ocr.ocr(image_path, cls=True)

# Print OCR result
print('OCR result -->', result)