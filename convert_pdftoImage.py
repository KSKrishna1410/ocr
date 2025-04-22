# import fitz
import os
from PIL import Image
from pdf2image import convert_from_path
import numpy as np
import re
import json


# Get the current script directory
current_dir = os.path.dirname(os.path.abspath(__file__))
poppler_path = os.path.join(current_dir, "static/poppler-24.08.0", "Library", "bin")
# poppler_path = "/usr/bin"  # Poppler binaries are usually here
# os.environ["PATH"] += os.pathsep + poppler_path
print("Poppler Path:", poppler_path)

dpi = 300
zoom = dpi / 72
# magnify = fitz.Matrix(zoom, zoom)

def pdf2ImageMethod(input_folder, output_folder, files):
    print(f"📄 Processing File in Conversion method")
    os.makedirs(output_folder, exist_ok=True)
    image_paths = []  # List to store image paths
    # Process based on file type
    if files.lower().endswith(".pdf"):
        normalized_pdf_name = files.replace(" ", "_").lower()
        pdf_path = os.path.join(input_folder, files)
        file_path = os.path.join(input_folder, normalized_pdf_name)
        
        # Rename PDF file if needed
        # if pdf_path != file_path:
        #     os.rename(pdf_path, file_path)

        print(f"📄 Processing PDF: {file_path}")
        images = convert_from_path(file_path, poppler_path=poppler_path)
        # images = fitz.open(file_path)
        base_name = os.path.splitext(normalized_pdf_name)[0]  # Extract normalized filename

        # Loop through PDF pages
        for page_num, image in enumerate(images, start=1):
            output_path = os.path.join(output_folder, f"{base_name}-{page_num}.png")
            image.save(output_path)
            # pix = image.get_pixmap(matrix=magnify)
            # pix.save(output_path)
            print(f"Saved: {output_path}")
            # Store the image path
            image_paths.append(output_path)  # Store the image path

    # ✅ Handle Image Files
    elif files.lower().endswith((".jpg", ".jpeg", ".png")):
        input_path = os.path.join(input_folder, files)
        output_path = os.path.join(output_folder, files)  # Save in output folder

        print(f"🖼️ Processing Image: {input_path}")

        try:
            image = Image.open(input_path)

            # Save the image in output folder
            image.save(output_path)
            print(f"✅ Image saved: {output_path}")
            # Store the image path
            image_paths.append(output_path)
            # Call the processing function
            # process_image_paddle(image)

        except Exception as e:
            print(f"❌ Error opening image: {e}")
    
    else:
        print(f"❌ Error: Unsupported file format '{files.lower()}'.")
    return image_paths  # Return list of image paths for further processing