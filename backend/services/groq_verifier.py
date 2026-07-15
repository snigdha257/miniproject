"""
backend/services/groq_verifier.py

Verification and recommendation service using the Groq API.
Reviews standard entities and detects missed sensitive entities.
"""

import json
import os
import urllib.request
import urllib.error
from typing import List, Dict

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def verify_with_groq(text: str, entities: List[Dict]) -> List[Dict]:
    """
    Calls Groq API to verify detected entities, recommend masking,
    and find any sensitive data missed by standard tools.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[GROQ] Warning: GROQ_API_KEY not configured. Defaulting all entities to recommendMask=True.")
        return [
            {
                "text": ent["text"],
                "label": ent["label"],
                "recommendMask": True,
                "reason": "Defaulting to mask (Groq API key not configured).",
                "start": ent["start"],
                "end": ent["end"]
            }
            for ent in entities
        ]

    prompt = {
        "text": text,
        "detected_entities": [
            {
                "text": ent["text"],
                "label": ent["label"],
                "start": ent["start"],
                "end": ent["end"]
            }
            for ent in entities
        ]
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a sensitive data classifier. You analyze document text and a list of entities "
                    "detected by standard regex/NLP systems. For each entity, decide whether it should be masked "
                    "based on privacy relevance. Also, scan the text for any missed sensitive entities (e.g. Salary, "
                    "Joining Date, passwords, keys, etc.).\n"
                    "You must return ONLY a JSON object in this format:\n"
                    "{\n"
                    "  \"entities\": [\n"
                    "    {\n"
                    "      \"text\": \"entity text\",\n"
                    "      \"label\": \"ENTITY_LABEL\",\n"
                    "      \"recommendMask\": true,\n"
                    "      \"reason\": \"reason for recommendation\",\n"
                    "      \"start\": integer_start_index,\n"
                    "      \"end\": integer_end_index\n"
                    "    }\n"
                    "  ]\n"
                    "}"
                )
            },
            {
                "role": "user",
                "content": json.dumps(prompt)
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GROQ_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        # 15 seconds timeout
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            content = res_data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            raw_entities = parsed.get("entities", [])
            verified_entities = []
            
            for ent in raw_entities:
                t = ent.get("text")
                if not t or not isinstance(t, str):
                    continue
                label = ent.get("label", "UNKNOWN").upper()
                recommend_mask = ent.get("recommendMask", True)
                reason = ent.get("reason", "")
                start = ent.get("start")
                end = ent.get("end")
                
                # Verify start/end offsets match the text
                if isinstance(start, int) and isinstance(end, int) and start >= 0 and end <= len(text) and text[start:end] == t:
                    verified_entities.append({
                        "text": t,
                        "label": label,
                        "recommendMask": recommend_mask,
                        "reason": reason,
                        "start": start,
                        "end": end
                    })
                else:
                    # Look up correct offsets for this substring in the text
                    idx = text.find(t)
                    if idx != -1:
                        verified_entities.append({
                            "text": t,
                            "label": label,
                            "recommendMask": recommend_mask,
                            "reason": reason,
                            "start": idx,
                            "end": idx + len(t)
                        })
            return verified_entities

    except Exception as e:
        print(f"[GROQ] Error calling Groq API: {e}. Falling back to standard pipeline.")
        return [
            {
                "text": ent["text"],
                "label": ent["label"],
                "recommendMask": True,
                "reason": f"Defaulting to mask (Groq call failed: {e}).",
                "start": ent["start"],
                "end": ent["end"]
            }
            for ent in entities
        ]
