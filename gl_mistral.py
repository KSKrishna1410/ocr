import ollama
import os

instruction = """
You are an AI that extracts structured information from invoice Raw text data.

    **Task:** Identify key-value pairs from the extracted text.
    - The **key** is the field name (e.g., "Invoice Number", "Total Amount").
    - The **value** is the extracted information.
    - **Always return the result as a valid JSON object** with standard field names.
    - **Do not include any nested JSON structures.**  
    - **Return a list of JSON objects in a completely flat format** with only key-value pairs.
    - **If a value is missing, return `"null"` instead of skipping it.**  

"""

output_format = """
    {
        "Invoice Number": "INV12345",
        "Invoice Date": "YYYY-MM-DD",
        "Customer Name": "XYZ Ltd.",
        "Total Amount": "2500.00",
        "Due Date": "YYYY-MM-DD"
        line_details : [{
            item:
            Qty:
            rate:
            line amount:
            tax:
            tax amount:
            
        }]
    }

    **Response Format Rules:**
    - **Return only JSON**, nothing else.
    - **No explanations**, no additional text.
    - **If a field is missing, return null instead of skipping it.**
"""
# aiResponse = analyze_text_with_ai(invoice_extracted_data,  instruction, output_format)

# aiResponse = analyze_text_with_ai(text,  task="Given is the Invoice Content, Identify Indian Invoice feild and value and return in JSON as a Key and value")

def passInstformat():
    aiObj = {
        "instruction": instruction,
        "outputFormat": output_format
    }
    return aiObj
# aiRes = passInstformat()
# print('Response -> ', aiRes)

# Function to process text with AI (Ollama)
def analyze_text_with_ai(invoice_extracted_data):
    query = f"{instruction} **Extracted Text:**  {invoice_extracted_data} and **Expected Output Format (Strict JSON):** {output_format}"
    # response = ollama.chat(model="mistral", messages=[{"role": "user", "content": query}])
    response = ollama.chat(model="llama3.3", messages=[{"role": "user", "content": query}])
    return response['message'] if response else "AI processing failed."


def read_env_variables():
    table_model_version = os.getenv("TABLE_MODEL_VERSION", "default_version")
    ocr_engine = os.getenv("OCR_ENGINE", "default_engine")
    debug_mode = os.getenv("DEBUG_MODE", "False") == "True"
    sftp_host = os.getenv("SFTP_HOST", "206")

    print(f"📦 Model Version: {table_model_version}")
    print(f"🔍 OCR Engine: {ocr_engine}")
    print(f"🐞 Debug Mode Enabled: {debug_mode}")
    print(f"🐞 SFTP Host : {sftp_host}")
    
read_env_variables()