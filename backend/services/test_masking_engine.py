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
