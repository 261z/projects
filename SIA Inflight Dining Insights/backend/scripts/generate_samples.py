import json
from pathlib import Path

routes = [("SIN–LHR", "Singapore–London"), ("SIN–JFK", "Singapore–New York"), ("SIN–CDG", "Singapore–Paris"), ("SIN–FRA", "Singapore–Frankfurt"), ("SIN–SFO", "Singapore–San Francisco"), ("SIN–SYD", "Singapore–Sydney")]
cabins = ["Economy", "Premium Economy", "Business", "First"]
meals = ["braised chicken rice", "fish with noodles", "vegetarian biryani", "beef rendang", "mushroom pasta", "congee", "salmon with quinoa"]
positives = ["The chicken was tender and the sauce was shiok, genuinely enjoyed it.", "Warm, tasty and nicely seasoned — a pleasant surprise at 35,000 feet.", "Loved the vegetarian option, very fresh and not boring at all.", "The breakfast congee was comforting and the fruit tasted fresh.", "Presentation was lovely and the crew checked in at the right time.", "Honestly excellent: fragrant, balanced and generous. I would happily order this again.", "Best airline meal I have had in ages — fluffy rice, tender meat and a really fresh salad.", "Superb from first bite to last, very shiok and thoughtfully seasoned.", "The dessert was delicious, the main was perfect, and the whole tray felt premium."]
neutral = ["Meal was served on time. Portion and presentation were as described; no strong preference.", "I had the pasta at the scheduled meal service. It was an ordinary, acceptable flight meal.", "The tray was complete and the flavour was straightforward. Nothing especially memorable.", "Food arrived with the standard service. I would consider other options next time.", "The meal met expectations for a long-haul flight; no particular comment on the taste."]
negatives = ["Main was cold by the time it reached me and the rice was dry.", "So salty until cannot finish, plus the portion was quite small.", "Fish was rubbery and the vegetables soggy — not the best start to a long flight.", "The vegetarian choice was missing and I had to wait; quite jialat.", "Looks premium, tastes like a sad microwave apology. Very dry."]
mixed = ["Dessert was excellent but the main was bland and lukewarm.", "Chicken flavour was good, however the portion left me hungry.", "Crew were kind, but my meal arrived late and cold.", "Nice presentation, though the noodles were soggy and too sweet."]
special = ["I have a peanut allergy and the tray label was unclear. Please review urgently.", "Found a small piece of plastic in the meal — food safety review needed.", "I am diabetic; the sugar information was not clear on the menu.", "No issue with taste, just wanted a clearer halal and vegetarian label."]

def make(i):
    route, city = routes[i % len(routes)]
    cabin = cabins[(i * 3) % len(cabins)]
    meal = meals[i % len(meals)]
    kind = (i + 1) % 20
    text = special[i % len(special)] if kind == 19 else positives[i % len(positives)] if kind <= 9 else neutral[i % len(neutral)] if kind <= 14 else negatives[i % len(negatives)] if kind <= 18 else mixed[i % len(mixed)]
    return {"review_id": f"SYN-{i+1:04d}", "review": text, "route": route, "destination": city, "cabin": cabin, "flight_date": f"2026-{(i%9)+1:02d}-{(i%27)+1:02d}", "language": ["English", "Singlish", "Mandarin-English", "Malay-English", "French-English"][i % 5], "meal": meal, "seat": f"{(i%40)+1}{'A' if i%2 else 'K'}", "loyalty_tier": ["KrisFlyer", "Elite Silver", "Elite Gold", "PPS Club"][i % 4]}

root = Path(__file__).resolve().parents[1] / "data"
root.mkdir(exist_ok=True)
for name, count in (("a", 1), ("b", 30), ("c", 200)):
    (root / f"sample_{name}.json").write_text(json.dumps([make(i) for i in range(count)], ensure_ascii=False, indent=2))
