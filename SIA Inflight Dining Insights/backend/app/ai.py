import json
import os

SCHEMA = {
    "type": "object",
    "properties": {"sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]}, "topics": {"type": "array", "items": {"type": "string"}}, "safety_flags": {"type": "array", "items": {"type": "string"}}},
    "required": ["sentiment", "topics", "safety_flags"], "additionalProperties": False,
}

def responses_api_label(review):
    """Optional structured-output call. The deterministic analyzer remains the source of truth offline."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=[{"role": "system", "content": "Classify this synthetic airline meal review. Return only the requested JSON."}, {"role": "user", "content": review}],
            text={"format": {"type": "json_schema", "name": "meal_review_label", "schema": SCHEMA, "strict": True}},
        )
        return json.loads(response.output_text)
    except Exception:
        return None
