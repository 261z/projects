import csv
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from docx import Document

OUT = Path(__file__).parent / "upload_fixtures"
OUT.mkdir(parents=True, exist_ok=True)
routes = ["SIN-LHR", "SIN-JFK", "SIN-CDG", "SIN-FRA", "SIN-SFO", "SIN-SYD"]
cabins = ["Economy", "Premium Economy", "Business", "First"]
meals = ["braised chicken rice", "fish with noodles", "vegetarian biryani", "beef rendang", "mushroom pasta", "salmon with quinoa"]
negative = [
    "The main was cold and the rice was dry; very disappointing for a long flight.",
    "Too salty and the portion was small, so I stayed hungry. Really not good.",
    "The fish was rubbery and the vegetables were soggy. This meal was awful.",
    "My meal arrived late and cold, with a missing side. Very poor experience.",
    "Looks premium, tastes like a sad microwave apology. Bland and dry.",
    "The sauce was burnt and the texture was unpleasant. I could not finish it.",
]
neutral = [
    "The meal arrived at the scheduled service. Portion was standard and I have no additional comment.",
    "I had the listed meal during the flight. It was an ordinary, acceptable option.",
    "The tray was complete and the flavour was straightforward. Nothing especially memorable.",
    "Food arrived with the standard service. I would consider another option next time.",
    "The meal met expectations for a long-haul flight; no particular comment on taste.",
]
positive = [
    "The meal was delicious, fresh and beautifully presented. I would happily order it again.",
    "Warm, tasty and nicely seasoned — a genuinely excellent surprise at 35,000 feet.",
    "Loved the vegetarian option; it was fresh, creamy and very satisfying.",
    "The breakfast was superb, the fruit was fresh and the portion was generous.",
    "Absolutely wonderful meal: fragrant, balanced and delicious from first bite to last.",
    "The crew timing was great and the food was perfect. Really enjoyed the whole tray.",
]

def records(count, kind, prefix):
    pool = {"negative": negative, "neutral": neutral, "positive": positive}[kind]
    return [{"review_id": f"{prefix}-{i+1:04d}", "review": pool[i % len(pool)], "route": routes[i % len(routes)], "cabin": cabins[(i * 3) % len(cabins)], "flight_date": f"2026-{(i % 9) + 1:02d}-{(i % 27) + 1:02d}", "language": ["English", "Singlish", "Mandarin-English", "Malay-English"][i % 4], "meal": meals[i % len(meals)]} for i in range(count)]

def text_lines(rows):
    return "\n".join(f"{row['review_id']}\t{row['review']}" for row in rows) + "\n"

csv_rows = records(250, "negative", "UPLOAD-CSV")
with (OUT / "upload_negative_250.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=csv_rows[0].keys())
    writer.writeheader(); writer.writerows(csv_rows)

pdf_rows = records(100, "neutral", "UPLOAD-PDF")
pdf = SimpleDocTemplate(str(OUT / "upload_neutral_100.pdf"), pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
styles = getSampleStyleSheet(); story = [Paragraph("SIA Inflight Dining Insights - Neutral Upload Fixture (100 reviews)", styles["Title"]), Spacer(1, 5*mm)]
for row in pdf_rows: story.append(Paragraph(f"{row['review_id']} | {row['review']}", styles["BodyText"])); story.append(Spacer(1, 1.5*mm))
pdf.build(story)

txt_rows = records(300, "positive", "UPLOAD-TXT")
(OUT / "upload_positive_300.txt").write_text(text_lines(txt_rows), encoding="utf-8")

doc_rows = records(450, "positive", "UPLOAD-DOCX")
doc = Document(); doc.add_heading("SIA Inflight Dining Insights - Positive Upload Fixture", level=1); doc.add_paragraph("Synthetic test file: 450 positive long-haul meal reviews.")
for row in doc_rows: doc.add_paragraph(f"{row['review_id']}\t{row['review']}")
doc.save(OUT / "upload_positive_450.docx")

print(f"Created {len(csv_rows)} CSV, {len(pdf_rows)} PDF, {len(txt_rows)} TXT, and {len(doc_rows)} DOCX reviews in {OUT}")
