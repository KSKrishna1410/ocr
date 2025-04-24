import re

def getKeylist(actual_ocr_output, key_mapping):
    """
    Extracts detected keys and their bounding boxes from OCR output based on predefined key variations.

    Parameters:
        actual_ocr_output: OCR extracted data (list of tuples: (bbox, (text, confidence)))
        key_mapping: Dictionary mapping standard keys to their possible variations

    Returns:
        List of matched key names and their bounding boxes.
    """
    matched_keys = []
    matched_keys_list = []
    document_text_list = [entry[1][0].lower() for entry in actual_ocr_output[0]]

    document_text_lower = "\n".join(document_text_list)  # Convert list to single string

    # Preprocess key mapping into regex patterns
    variation_to_standard = {}
    regex_patterns = []
    
    print('Before regex pattern check',  key_mapping.items())
    for standard_key, variations in key_mapping.items():
        for variant in variations:
            pattern = rf"\b{re.escape(variant.lower())}\b"
            regex_patterns.append((pattern, standard_key, variant))
            # print(f"Matched pattern  -> '{pattern}' -> standard_key '{standard_key}' and the Varaint {variant}")
            variation_to_standard[variant.lower()] = standard_key
    print('After regex pattern check',  regex_patterns)
    
    
    
    # Use regex to find all matches at once
    print('Document TExt ----- > ', document_text_lower)
    for pattern, standard_key, variant in regex_patterns:
        matches = re.finditer(pattern, document_text_lower)
        
        for match in matches:
            matched_keys.append({
                "key": variant,
                "standard_key": standard_key,
                "key_bounding_box": None,  # Will be assigned later
                "value": None,
                "value_bounding_box": None,
                "method":None
            })
            # print(f"Matched '{variant}' -> '{standard_key}'")

    # Map bounding boxes in one loop
    for entry in actual_ocr_output[0]:
        bbox, (text, confidence) = entry
        text_lower = text.lower()
        text_lower = re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$", "", text_lower.strip())
        match = re.match(r"(.+?)\s*:\s*(.+)", text)
        # re.compile(r"([\w\s]+):\s*(.+)", re.IGNORECASE)
        if match:
            print('colon_identification detect for ', text_lower)
            key, value = match.groups()  # Extract pre-text (key) and post-text (value)
            for matched_key in matched_keys:
                if "key" in matched_key and matched_key["key"].lower() == key.lower():
                    matched_key["value"] = value
                    matched_key["key_bounding_box"] = str(bbox)
                    matched_key["method"] = 'colon_identification'
                    print(f"matched_key Bounding Box Assigned using colon_identification -> '{text}': {bbox} and key {key.lower()} and the Value is {value}")
            # matched_key_values = {"key": key.strip(), "value": value.strip()}  # Store in dictionary
            # print(f"Line After🔹 🔹 🔹 matched_keys '{matched_keys}'")
        if text_lower in variation_to_standard:
            for matched_key in matched_keys:
                if matched_key["key"].lower() == text_lower and matched_key.get("key_bounding_box") is None:
                    matched_key["key_bounding_box"] = str(bbox)
                    break
    # print(f"Before🔹 🔹 🔹 matched_keys '{matched_keys}'")
    for matched_key in matched_keys:
        matched_keys_list.append(f"{matched_key['key']} -- {matched_key['standard_key']}")
    print(f"After🔹 🔹 🔹 matched_keys '{matched_keys}'")
    return matched_keys