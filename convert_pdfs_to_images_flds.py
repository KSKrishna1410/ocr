import fitz
import os

# Input and output folder paths
input_folder = r"C:\Users\nisha\Documents\ProductDevelopement\genAI\Bank_STmt"  # Folder containing PDFs
output_folder = r"C:\Users\nisha\Documents\ProductDevelopement\genAI\Bank_STmt/images"  # Folder to save PNGs

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

dpi = 300
zoom = dpi / 72
magnify = fitz.Matrix(zoom, zoom)

# Loop through all PDF files in the input folder
for pdf_file in os.listdir(input_folder):
    if pdf_file.lower().endswith(".pdf"):
        normalized_pdf_name = pdf_file.replace(" ", "_").lower()
        pdf_path = os.path.join(input_folder, pdf_file)
        new_pdf_path = os.path.join(input_folder, normalized_pdf_name)
        os.rename(pdf_path, new_pdf_path)  # Rename the PDF file
        
        doc = fitz.open(new_pdf_path)
        base_name = os.path.splitext(normalized_pdf_name)[0]  # Extract normalized filename
        
        for page_num, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=magnify)
            output_path = os.path.join(output_folder, f"{base_name}-{page_num}.png")
            pix.save(output_path)
            print(f"Saved: {output_path}")
