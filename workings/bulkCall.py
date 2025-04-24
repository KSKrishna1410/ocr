import os
import shutil
from main import main  # main must be a callable function in main.py

input_folder = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\tabula_invoice_test_results\Processed"
output_base = r"C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\tabula_invoice_test"

for filename in os.listdir(input_folder):
    print(f"Processing file: {filename}")
    if filename.lower().endswith(".pdf"):
        input_file_path = os.path.join(input_folder, filename)
        file_name_without_ext = os.path.splitext(filename)[0]

        output_folder_path = os.path.join(output_base, file_name_without_ext)
        os.makedirs(output_folder_path, exist_ok=True)

        moved_file_path = os.path.join(output_folder_path, filename)
        shutil.copy(input_file_path, moved_file_path)

        print(f"Processing file: {moved_file_path}")
        print(f"Output will be stored in: {output_folder_path}")

        try:
            main(output_folder_path, output_folder_path, 'invoice')  # Correct call
            print(f"✔️ Successfully processed {filename}\n")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}\n")
