# OCR Extraction using PaddleOCR & Tabula

## Overview
This project is a Python-based solution for extracting structured information from PDFs and images (**JPG, PNG**) using **PaddleOCR**. It applies three key algorithms to extract **header data** as key-value pairs and utilizes **Tabula** to extract tabular data from documents.

## Features
- Extracts text from PDFs and images (**JPG, PNG**) using **PaddleOCR**.
- Applies three OCR processing algorithms to extract key-value pairs from header data:
  - **Right-Aligned Method**
  - **Bottom-Aligned Method**
  - **Colon Method**
- Uses **Tabula** for table extraction from PDF files.
- Returns structured output in JSON format.

## Installation
### Prerequisites
Ensure you have **Python 3.7+** installed. Install the required dependencies using:
```bash
pip install -r requirements.txt
```

### Required Packages
The project relies on the following key libraries:
- **paddleocr** - For Optical Character Recognition (OCR)
- **tabula-py** - For extracting tables from PDFs
- **opencv-python** - Image processing support
- **numpy** - Array operations
- **pandas** - Data manipulation

## Usage
### Extract Text and Structure Data
Run the following command to extract data from a file:
```bash
python main.py <input_folder_path> <output_folder_path> <doc_type>
```
Example:
```bash
python .\main.py "C:\Users\Documents\PaddleOCR_research\inputs" "C:\Users\Documents\PaddleOCR_research\inputs\images" invoice
```

### Sample JSON Output
```json
{
    "headerData": [
        {
            "page": 1,
            "extractedData": [
                {
                    "key": "Invoice Amount",
                    "value": "Discount",
                    "key_bbox": [[554.0, 843.0], [652.0, 843.0], [652.0, 870.0], [554.0, 870.0]],
                    "value_bbox": [[668.0, 835.0], [820.0, 841.0], [819.0, 875.0], [667.0, 869.0]],
                    "method": "right_aligned_pair",
                    "doc_text": "Gross",
                    "closest_distance": 140.50
                }
            ]
        }
    ],
    "lineTabulaData": []
}
```

## Methods Used
1. **Right-Aligned Pair:** Extracts key-value pairs aligned horizontally.
2. **Bottom-Aligned Pair:** Extracts key-value pairs stacked vertically.
3. **Colon Method:** Extracts key-value pairs separated by a colon (':').

## Contributing
Feel free to contribute by submitting issues or pull requests.

## License
This project is licensed under the **MIT License**.


# python .\main.py "C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\inputs" "C:\Users\nisha\Documents\ProductDevelopement\OpenSourceModel\PaddleOCR_research\std_code\v3\inputs\images"


