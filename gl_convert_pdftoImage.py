# import fitz
import os
from PIL import Image
from pdf2image import convert_from_path
import numpy as np
import re
import json
from io import BytesIO
from gl_utilities import upload_to_sftp
# Get the current script directory
current_dir = os.path.dirname(os.path.abspath(__file__))
poppler_path = os.path.join(current_dir, "poppler-24.08.0", "Library", "bin")
# print("Poppler Path:", poppler_path)

dpi = 300
zoom = dpi / 72
# magnify = fitz.Matrix(zoom, zoom)

def pdf2ImageMethod(input_folder, remote_dir, output_folder, file):
    print(f"📄 Processing File in Conversion method")
    image_paths = []  # List to store image paths

    if file.lower().endswith(".pdf"):
        normalized_pdf_name = file.replace(" ", "_").lower()
        file_path = os.path.join(input_folder, normalized_pdf_name)

        print(f"📄 Processing PDF: {file_path}")
        images = convert_from_path(file_path)
        base_name = os.path.splitext(normalized_pdf_name)[0]

        for page_num, image in enumerate(images, start=1):
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            r_image_path = upload_to_sftp(buffer.read(), f"{base_name}-{page_num}.png", remote_dir)
            print(f"✅ Uploaded: {r_image_path}")
            
            output_path = os.path.join(output_folder, f"{base_name}-{page_num}.png")
            image.save(output_path)
            image_paths.append(output_path)

    elif file.lower().endswith((".jpg", ".jpeg", ".png")):
        input_path = os.path.join(input_folder, file)
        print(f"🖼️ Processing Image: {input_path}")

        try:
            image = Image.open(input_path)
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            remote_image_path = upload_to_sftp(buffer.read(), file, remote_dir)
            print(f"✅ Uploaded: {remote_image_path}")
                        # Save the image in output folder
            image.save(output_path)
            print(f"✅ Image saved: {output_path}")
            # Store the image path
            image_paths.append(output_path)

        except Exception as e:
            print(f"❌ Error opening image: {e}")

    else:
        print(f"❌ Error: Unsupported file format '{file.lower()}'.")

    return image_paths
