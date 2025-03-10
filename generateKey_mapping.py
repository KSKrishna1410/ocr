import csv

def generate_key_mapping(doctype):
    key_mapping = {}
    # Usage
    if doctype.lower() == 'invoice':
        csv_file_path = "inputs/Invoice_keys.csv"  # file path
    elif doctype.lower() == 'bankstmt':
        csv_file_path = "inputs/bankstmt_keys.csv"  # file path
    # Read the CSV file
    with open(csv_file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            key, doc_text = row[0].strip(), row[1].strip()

            # Append doc_text to the corresponding key in key_mapping
            if key in key_mapping:
                key_mapping[key].append(doc_text)
            else:
                key_mapping[key] = [doc_text]

    return key_mapping


# key_mapping = generate_key_mapping()

# Print the dictionary
# print("key_mapping =", key_mapping)