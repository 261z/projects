import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

def get_sample(name):
    if name not in {"a", "b", "c"}:
        raise ValueError("sample must be a, b, or c")
    return json.loads((DATA / f"sample_{name}.json").read_text())
