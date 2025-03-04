import re

def getKeylist(actual_ocr_putput, key_mapping):
    # Extract detected text from OCR output (convert to lowercase)
    document_text_list = [entry[1][0].lower() for entry in actual_ocr_putput[0]]
    document_text_lower = "\n".join(document_text_list)  # Convert list to single string

    # Store identified keys in the document
    doc_key_list = []
    std_key_list = []
    # Check if any variations of keys are present in the document
    # "invoice_number": ["Invoice#","invoice number","Invoice#", "invoice no", "bill number"],
    for standard_key, variations in key_mapping.items():
        for variant in variations:
            pattern = rf"\b{re.escape(variant.lower())}\b"  # Use regex for exact word matching
            if re.search(pattern, document_text_lower):
                doc_key_list.append(variant)  # Append standard key
                std_key_list.append(standard_key)  # Append standard key
                
                print(f"Matched '{variant}' -> '{standard_key}'")  # Debugging output
                break  # Stop checking other variations once a match is found

    # The full list of possible keys
    KEY_LIST = list(key_mapping.keys())

    # Find keys that were not matched
    not_matched_keys = [key for key in KEY_LIST if key not in std_key_list]

    # Print results
    print("\nKEY_LIST =", KEY_LIST)
    print("\ndoc_key_list =", doc_key_list)
    print("\nstd_key_list =", std_key_list)
    print("\nnot_matched_keys =", not_matched_keys)

    return doc_key_list