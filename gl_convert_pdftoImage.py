# import fitz
import os
import PyPDF2

from PIL import Image
from pdf2image import convert_from_path
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
    file_path = os.path.join(input_folder, file)
    fileType = ''
    base_name = os.path.splitext(file)[0]
    print(f"🖼️ Processing Image: {file_path}")
    if file.lower().endswith(".pdf"):
        # normalized_pdf_name = file.replace(" ", "_").lower()
        # file_path = os.path.join(input_folder, normalized_pdf_name)
        fileType = is_scanned_pdf(file_path)
        print(f"📄 Processing PDF: {file_path} and the PDF type is {fileType}")
        images = convert_from_path(file_path)

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
        fileType = "Image"
        output_path = os.path.join(output_folder, f"{base_name}.png")
        try:
            image = Image.open(file_path)
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

    return image_paths, fileType


def is_scanned_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            print('Inside PDF Document ------>',  page)
            try:
                if '/Font' in page['/Resources']:
                    return "System-generated"
                elif '/XObject' in page['/Resources']:
                    xObject = page['/Resources']['/XObject'].get_object()
                    for obj in xObject:
                        if xObject[obj]['/Subtype'] == '/Image':
                            return "Scanned"
            except:
                continue
    return "Unknown"

def get_pdf_page_classification(file_path):
    page_results = []

    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page_num, page in enumerate(reader.pages, start=1):
            result = "Unknown"
            try:
                resources = page.get('/Resources', {})
                
                # Check for fonts
                if '/Font' in resources:
                    result = "System-generated"
                
                # Check for images
                elif '/XObject' in resources:
                    xObject = resources['/XObject'].get_object()
                    for obj in xObject:
                        if xObject[obj].get('/Subtype') == '/Image':
                            result = "Scanned"
                            break  # Once image is found, it's scanned
            except Exception as e:
                result = f"Error: {str(e)}"

            page_results.append({
                "page": page_num,
                "type": result
            })

    return page_results
