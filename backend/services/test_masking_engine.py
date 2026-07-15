from masking_engine import mask_text


def test_mask_text_exact_sample():
    text = "John Doe from Google (john.doe@gmail.com)"
    entities = [
        {"text": "John Doe", "label": "PERSON", "start": 0, "end": 8},
        {"text": "Google", "label": "ORG", "start": 14, "end": 20},
        {"text": "john.doe@gmail.com", "label": "EMAIL", "start": 22, "end": 40},
    ]

    full_expected = "████████ from ██████ (██████████████████)"
    placeholder_expected = "<Person_1> from <Org_1> (<Email_1>)"
    partial_expected = "J*** D** from G****e (j***.d**@gmail.com)"

    full = mask_text(text, entities, "full")
    placeholder = mask_text(text, entities, "placeholder")
    partial = mask_text(text, entities, "partial")

    assert full["masked_text"] == full_expected
    assert placeholder["masked_text"] == placeholder_expected
    assert partial["masked_text"] == partial_expected

    assert full["mapping"][0]["original"] == "John Doe"
    assert placeholder["mapping"][1]["replacement"] == "<Org_1>"
    assert partial["mapping"][2]["type"] == "EMAIL"


def test_mask_text_adjacent_entities():
    text = "JaneDoejanedoe@example.com is sensitive"
    entities = [
        {"text": "JaneDoe", "label": "PERSON", "start": 0, "end": 7},
        {"text": "janedoe@example.com", "label": "EMAIL", "start": 7, "end": 26},
    ]

    result = mask_text(text, entities, "full")
    assert result["masked_text"] == "██████████████████████████ is sensitive"
    assert result["mapping"][0]["position"] == (0, 7)
    assert result["mapping"][1]["position"] == (7, 26)


def test_mask_overlapping_and_duplicate_entities():
    text = "Microsoft Corporation is based in Redmond."
    entities = [
        {"text": "Microsoft Corporation", "label": "ORG", "start": 0, "end": 21},
        {"text": "Microsoft", "label": "ORG", "start": 0, "end": 9},
        {"text": "Microsoft", "label": "ORG", "start": 0, "end": 9},
    ]
    result = mask_text(text, entities, "full")
    assert result["masked_text"] == "█████████████████████ is based in Redmond."
    assert len(result["mapping"]) == 1
    assert result["mapping"][0]["original"] == "Microsoft Corporation"


def test_mask_all_entity_types():
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
        {"text": "1234 5678 9012", "label": "AADHAAR", "start": 118, "end": 132},
        {"text": "ABCDE1234F", "label": "PAN", "start": 141, "end": 151},
        {"text": "1234 5678 9012 3456", "label": "CREDIT_CARD", "start": 172, "end": 191},
    ]

    # Verify "full" mode
    full = mask_text(text, entities, "full")
    expected_full = (
        "Hello, my name is ███████████. "
        "My email is ███████████████████████ and phone is ███████████████. "
        "My Aadhaar number is ██████████████, PAN is ██████████, "
        "and credit card is ███████████████████."
    )
    assert full["masked_text"] == expected_full

    # Verify "placeholder" mode
    placeholder = mask_text(text, entities, "placeholder")
    expected_placeholder = (
        "Hello, my name is <Person_1>. "
        "My email is <Email_1> and phone is <Phone_1>. "
        "My Aadhaar number is <Aadhaar_1>, PAN is <PAN_1>, "
        "and credit card is <CreditCard_1>."
    )
    assert placeholder["masked_text"] == expected_placeholder

    # Verify "partial" mode
    partial = mask_text(text, entities, "partial")
    expected_partial = (
        "Hello, my name is A*** S*****. "
        "My email is a***.s*****@example.com and phone is +** 9**** 4****. "
        "My Aadhaar number is 1*** 5*** 9***, PAN is A*********, "
        "and credit card is 1*** 5*** 9*** 3***."
    )
    assert partial["masked_text"] == expected_partial

