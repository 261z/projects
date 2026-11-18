import re
from collections import Counter, defaultdict
from datetime import datetime

POSITIVE = {"delicious", "tasty", "great", "good", "fresh", "fluffy", "creamy", "perfect", "love", "loved", "nice", "yummy", "sedap", "shiok", "不错", "好吃", "美味"}
NEGATIVE = {"cold", "dry", "bland", "salty", "soggy", "rubbery", "stale", "burnt", "late", "missing", "disappointing", "awful", "bad", "worst", "meh", "tak", "jialat", "难吃", "太咸"}
TOPIC_TERMS = {"temperature": ["cold", "warm", "lukewarm", "heat", "温", "冷"], "flavour": ["bland", "salty", "sweet", "spicy", "taste", "flavour", "味", "咸"], "texture": ["dry", "soggy", "rubbery", "crispy", "texture", "硬"], "portion": ["portion", "small", "hungry", "serving", "份量"], "service": ["crew", "sorry", "late", "missing", "service", "荤素", "order"], "choice": ["choice", "option", "menu", "vegetarian", "vegan", "halal", "选"], "presentation": ["presentation", "looks", "tray", "packaging"]}
SAFETY_RULES = [("allergy", ["allerg", "peanut", "nut", "shellfish", "gluten", "intoleran"]), ("food_safety", ["raw", "spoilt", "spoiled", "mould", "mold", "foreign object", "hair", "contaminat"]), ("medical", ["diabetic", "medical", "celiac", "pregnant"]), ("serious_service", ["shouted", "discriminat", "unsafe", "emergency", "threat"])]

def _tokens(text):
    return re.findall(r"[a-zA-Z][a-zA-Z'-]+", text.lower())

def sentiment(text):
    tokens = _tokens(text)
    pos = sum(t in POSITIVE for t in tokens)
    neg = sum(t in NEGATIVE for t in tokens)
    if "but" in tokens or "however" in tokens:
        neg += 0.3
    score = pos - neg
    label = "positive" if score >= 1 else "negative" if score <= -1 else "neutral"
    return label, round(score, 2)

def classify_topics(text):
    low = text.lower()
    return [topic for topic, terms in TOPIC_TERMS.items() if any(term in low for term in terms)] or ["general"]

def safety_flags(text):
    low = text.lower()
    flags = []
    for label, terms in SAFETY_RULES:
        hits = [term for term in terms if term in low]
        if hits:
            flags.append({"type": label, "evidence": hits[:3], "severity": "high" if label in {"allergy", "food_safety", "medical"} else "medium", "action": "Human review required before operational follow-up."})
    return flags

def analyze_review(row):
    text = str(row.get("review", "")).strip()
    label, score = sentiment(text)
    return {**row, "review": text, "sentiment": label, "sentiment_score": score, "topics": classify_topics(text), "safety_flags": safety_flags(text)}

def analyze_batch(rows):
    analyzed = [analyze_review(row) for row in rows]
    total = len(analyzed)
    counts = Counter(row["sentiment"] for row in analyzed)
    topic_counts = Counter(topic for row in analyzed for topic in row["topics"] if topic != "general")
    words = Counter(token for row in analyzed for token in _tokens(row["review"]) if len(token) > 3 and token not in POSITIVE | NEGATIVE)
    recurring = [{"keyword": word, "count": count} for word, count in words.most_common(12) if count >= 2]
    if not recurring:
        recurring = [{"keyword": topic, "count": count} for topic, count in topic_counts.most_common(8)]
    health = round(((counts["positive"] + counts["neutral"] * 0.5) / total) * 100) if total else 0
    flags = [{"review_id": row.get("review_id", ""), "review": row["review"], **flag} for row in analyzed for flag in row["safety_flags"]]
    recommendations = build_recommendations(analyzed, topic_counts)
    return {"rows": analyzed, "kpis": {"total_reviews": total, "health_score": health, "positive": counts["positive"], "neutral": counts["neutral"], "negative": counts["negative"], "safety_flag_count": len(flags), "top_topics": [{"topic": k, "count": v} for k, v in topic_counts.most_common()]}, "recurring_keywords": recurring, "recommendations": recommendations, "safety_flags": flags, "analyzed_at": datetime.utcnow().isoformat() + "Z"}

def build_recommendations(rows, topics):
    neg_topics = Counter(topic for row in rows if row["sentiment"] == "negative" for topic in row["topics"])
    top = neg_topics.most_common(3)
    phrases = ", ".join(topic for topic, _ in top) or "overall meal satisfaction"
    return {
        "cabin_crew": [f"Add a mid-service temperature and missing-item check, prioritising {phrases}.", "Offer a concise acknowledgement and replacement path when a meal issue is reported.", "Briefly log allergy or safety concerns for human review; do not improvise ingredient assurances."],
        "catering_food_prep": [f"Audit long-haul handoff controls for {phrases}, especially hot-hold, texture, and portion consistency.", "Compare flagged routes and meal codes against prep, loading, and reheating checkpoints.", "Create a small corrective-action sample and re-measure after the next menu cycle."],
        "menu_design": [f"Test one menu iteration that addresses {phrases} while preserving dietary and cultural choice.", "Balance familiar comfort dishes with one lighter option and clearer menu descriptions.", "Use a rotating route/cabin pilot and compare health score, sentiment, and repeat keywords."],
    }
