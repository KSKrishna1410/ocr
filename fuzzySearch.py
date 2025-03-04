from fuzzywuzzy import fuzz

text = "Invoice Number 10725KD000042971"
key = "Invoice Number"

score = fuzz.partial_ratio(text.lower(), key.lower())

print(score)  # Output: 100 (since "Invoice Number" is fully contained in text)
