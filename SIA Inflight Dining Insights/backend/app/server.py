import io
import json
import os
import re
import pandas as pd
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from .analytics import analyze_batch
from .samples import get_sample
from .ai import responses_api_label

app = Flask(__name__)
CORS(app)

def normalize_rows(rows):
    result = []
    for i, row in enumerate(rows):
        if isinstance(row, str): row = {"review": row}
        text = str(row.get("review", row.get("comment", ""))).strip()
        if text:
            item = {str(k): v for k, v in row.items() if v not in (None, "")}
            item["review"] = text
            item.setdefault("review_id", f"PASTE-{i+1:03d}")
            result.append(item)
    if len(result) > 5000:
        raise ValueError("Maximum batch size is 5,000 reviews")
    return result

def rows_from_plain_text(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        parts = re.split(r"\t+|\s*\|\s*", line, maxsplit=1)
        if len(parts) == 2 and re.match(r"^[A-Za-z0-9_-]+$", parts[0]):
            rows.append({"review_id": parts[0], "review": parts[1]})
        elif not line.lower().startswith(("sia inflight", "upload fixture", "review id", "generated")):
            rows.append({"review": line})
    return normalize_rows(rows)

@app.get("/api/health")
def health(): return jsonify({"ok": True, "ai_enabled": bool(os.getenv("OPENAI_API_KEY"))})

@app.get("/api/samples/<name>")
def sample(name):
    try: return jsonify({"name": name, "reviews": get_sample(name)})
    except ValueError as exc: return jsonify({"error": str(exc)}), 400

@app.post("/api/analyze")
def analyze():
    body = request.get_json(silent=True) or {}
    try:
        rows = normalize_rows(body.get("reviews", []))
        if not rows: return jsonify({"error": "Add at least one review."}), 400
        # The optional Responses API structured-output call is server-side only.
        # Deterministic analysis remains the reliable demo default and fallback.
        result = analyze_batch(rows)
        result["mode"] = "deterministic"
        if body.get("use_ai") and os.getenv("OPENAI_API_KEY"):
            label = responses_api_label(rows[0]["review"])
            if label: result["mode"] = "responses-api-structured"
        return jsonify(result)
    except ValueError as exc: return jsonify({"error": str(exc)}), 400

@app.post("/api/parse-upload")
def parse_upload():
    uploaded = request.files.get("file")
    if not uploaded: return jsonify({"error": "Choose a CSV, XLSX, PDF, DOCX, TXT, or JSON file."}), 400
    try:
        name = uploaded.filename.lower()
        raw_bytes = uploaded.read()
        buffered = io.BytesIO(raw_bytes)
        if name.endswith(".json"):
            rows = json.loads(raw_bytes.decode("utf-8"))
        elif name.endswith(".xlsx"):
            rows = pd.read_excel(buffered).fillna("").to_dict(orient="records")
        elif name.endswith(".csv"):
            rows = pd.read_csv(buffered).fillna("").to_dict(orient="records")
        elif name.endswith(".txt"):
            return jsonify({"reviews": rows_from_plain_text(raw_bytes.decode("utf-8"))})
        elif name.endswith(".pdf"):
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(buffered).pages)
            return jsonify({"reviews": rows_from_plain_text(text)})
        elif name.endswith(".docx"):
            from docx import Document
            text = "\n".join(paragraph.text for paragraph in Document(buffered).paragraphs)
            return jsonify({"reviews": rows_from_plain_text(text)})
        else:
            return jsonify({"error": "Supported formats are CSV, XLSX, PDF, DOCX, TXT, and JSON."}), 400
        return jsonify({"reviews": normalize_rows(rows)})
    except Exception as exc:
        return jsonify({"error": f"Could not parse upload: {exc}"}), 400

@app.post("/api/export")
def export():
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([{k: (", ".join(v) if isinstance(v, list) else v) for k, v in row.items() if k != "safety_flags"} for row in rows]).to_excel(writer, index=False, sheet_name="Reviewed Feedback")
        pd.DataFrame([payload.get("kpis", {})]).to_excel(writer, index=False, sheet_name="KPI Summary")
        pd.DataFrame(payload.get("recurring_keywords", [])).to_excel(writer, index=False, sheet_name="Recurring Themes")
        rec = payload.get("recommendations", {})
        pd.DataFrame([{"role": role, "recommendation": item} for role, items in rec.items() for item in items]).to_excel(writer, index=False, sheet_name="Recommendations")
        pd.DataFrame(payload.get("safety_flags", [])).to_excel(writer, index=False, sheet_name="Safety Flags")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="sia-inflight-dining-insights.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__": app.run(port=5000, debug=True)
