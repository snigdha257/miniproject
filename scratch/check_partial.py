from backend.services.masking_engine import mask_text

text = (
    "Hello, my name is Amit Sharma. "
    "My email is amit.sharma@example.com and phone is +91 98765 43210. "
    "My Aadhaar number is 1234 5678 9012, PAN is ABCDE1234F, "
    "and credit card is 1234 5678 9012 3456."
)

entities = [
    {"text": "Amit Sharma", "label": "PERSON", "start": 18, "end": 29},
    {"text": "amit.sharma@example.com", "label": "EMAIL", "start": 43, "end": 66},
    {"text": "+91 98765 43210", "label": "PHONE", "start": 80, "end": 95},
    {"text": "1234 5678 9012", "label": "AADHAAR", "start": 116, "end": 130},
    {"text": "ABCDE1234F", "label": "PAN", "start": 139, "end": 149},
    {"text": "1234 5678 9012 3456", "label": "CREDIT_CARD", "start": 170, "end": 189},
]

partial = mask_text(text, entities, "partial")
print("PARTIAL MASKED TEXT:")
print(partial["masked_text"])
