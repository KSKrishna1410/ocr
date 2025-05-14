from difflib import SequenceMatcher
import re

def normalize(text):
    # return re.sub(r"[^a-z0-9 ]+", "", text.lower().strip())
    # return re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', text.lower().strip())
    return text.lower().strip()

def get_best_match(text, key_mapping, threshold=0.85):
    normalized_text = normalize(text)

    # Step 1: Try exact match first
    for standard_key, variants in key_mapping.items():
        for variant in variants:
            if normalize(variant) == normalized_text:
                # print(f"Exact Match record ------> normalized_text {normalized_text} and the variant is {variant}" )
                return standard_key, variant

    # Step 2: Fallback to best fuzzy match
    # best_score = 0
    # best_standard_key = None
    # best_variant = None

    # for standard_key, variants in key_mapping.items():
    #     for variant in variants:
    #         score = SequenceMatcher(None, normalized_text, normalize(variant)).ratio()
    #         if score > best_score:
    #             best_score = score
    #             best_standard_key = standard_key
    #             best_variant = variant

    # if best_score >= threshold:
    #     return best_standard_key, best_variant

    return None, None

def getKeylist(actual_ocr_output, key_mapping, doc_text_lables):
    matched_keys = []
    colon_matched_keys = []
    direct_matched_keys = []

    text_entries = actual_ocr_output[0]  # Assuming a flat list of OCR output

    for bbox, (text, confidence) in text_entries:
        normalized_text = normalize(text)
        is_colon_detect = False
        # Handle colon-based key-value detection: key: value
        colon_match = re.match(r"^\s*(.+?)\s*[:#]\s*(.+?)\s*$", text)
        # colon_match = re.match(r"^\s*(.+?)\s*:\s*(.+?)\s*$", text)
        if colon_match:
            parts = re.split(r'[:#]', text, maxsplit=1)
            print(f' Key is identifued as parts {parts} for the text {text}')
            key_part = parts[0].strip()
            value_part = parts[1].strip() if parts[1] else ''
            is_colon_detect = True
            if normalize(value_part) in [re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', kw.lower().strip()) for kw in doc_text_lables]:
                print(f' Skipping Colon detection an value matched with Key lables')
                is_colon_detect = False
        
        if is_colon_detect: 
            standard_key, variant = get_best_match(key_part, key_mapping)
            if standard_key:
                matched_keys.append({
                    "key": variant,
                    "standard_key": standard_key,
                    "key_bounding_box": str(bbox),
                    "value": value_part,
                    "value_bounding_box": None,
                    "method": "colon_identification"
                })
                colon_matched_keys.append(variant)
                print(f"[COLON DETECTED] Matched: '{key_part}' -> '{standard_key}' | Value: '{value_part}'")
        else:
            # Try to match individual text without a colon (e.g., keys in isolation)
            standard_key, variant = get_best_match(text, key_mapping)
            if standard_key:
                existing_entry = next((k for k in matched_keys if k["key"] == variant), None)
                if not existing_entry:
                    matched_keys.append({
                        "key": variant,
                        "standard_key": standard_key,
                        "key_bounding_box": str(bbox),
                        "value": None,
                        "value_bounding_box": None,
                        "method": "direct_match"
                    })
                    direct_matched_keys.append(variant)
                    print(f"[DIRECT MATCH] Key-only matched: '{text}' -> '{standard_key}'")

    # Summary debug logs
    print("\n🔹 Colon-based Matched Keys:")
    for key in colon_matched_keys:
        print(f"  ➤ {key}")

    print("\n🔸 Direct Matched Keys (No value yet):")
    for key in direct_matched_keys:
        print(f"  ➤ {key}")

    return matched_keys
