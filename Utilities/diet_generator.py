import re
import spacy

_nlp = spacy.blank("en")
if "sentencizer" not in _nlp.pipe_names:
    _nlp.add_pipe("sentencizer")

DISEASE_KEYWORDS = {
    "diabetes": ["diabetes", "high sugar", "hyperglycemia"],
    "hypertension": ["hypertension", "blood pressure", "bp"],
    "cholesterol": ["cholesterol", "ldl", "hdl", "triglycerides", "hyperlipidemia"],
}

DIET_HINTS = [
    "diet", "eat", "avoid", "limit", "reduce", "increase", "fiber",
    "sugar", "salt", "oil", "fried", "whole grain", "vegetables", "fruit",
]

LIFESTYLE_HINTS = [
    "exercise", "walk", "running", "yoga", "sleep", "stress", "hydrate",
    "water", "daily", "activity", "active",
]

def _segment(text):
    doc = _nlp.make_doc(text)
    # use sentencizer
    for s in _nlp.get_pipe("sentencizer")(doc).sents:
        yield s.text.strip()

def _contains_any(s, words):
    s = s.lower()
    return any(w in s for w in words)

def _extract_avoids(sent):
    m = re.findall(r"(avoid|limit|reduce)\s+([a-zA-Z ]+)", sent.lower())
    foods = []
    for _, phrase in m:
        phrase = phrase.strip().strip(".")
        if len(phrase) <= 40:
            foods.append(phrase)
    return foods

def generate_diet(text):
    text = (text or "").strip()
    if not text:
        return {
            "condition": "General Health",
            "allowed_foods": ["vegetables", "whole grains", "fruits"],
            "restricted_foods": [],
            "diet_plan": "Maintain a balanced and healthy diet.",
            "lifestyle_advice": "Stay active and hydrated.",
        }
    lower = text.lower()
    sentences = list(_segment(lower))
    diseases_found = set()
    for label, kws in DISEASE_KEYWORDS.items():
        if _contains_any(lower, kws):
            diseases_found.add(label.capitalize())
    diet_advice_sents = []
    lifestyle_sents = []
    restricted = set()
    for s in sentences:
        if _contains_any(s, DIET_HINTS):
            diet_advice_sents.append(s)
            for f in _extract_avoids(s):
                restricted.add(f)
        if _contains_any(s, LIFESTYLE_HINTS):
            lifestyle_sents.append(s)
    allowed = set(["vegetables", "whole grains", "fruits"])
    if "Diabetes" in diseases_found:
        restricted.add("sugar")
        allowed.update(["legumes", "nuts", "low-glycemic fruits"])
    if "Cholesterol" in diseases_found:
        restricted.add("fried food")
        restricted.add("high saturated fat")
        allowed.update(["oats", "barley", "olive oil"])
    if "Hypertension" in diseases_found:
        restricted.add("salt")
        allowed.update(["leafy greens", "bananas", "yogurt"])
    if not diseases_found:
        diseases_found.add("General Health")
    diet_plan_text = " ".join(diet_advice_sents).strip()
    if not diet_plan_text:
        diet_plan_text = "Follow a balanced, high-fiber, nutrient-dense diet."
    lifestyle_text = " ".join(lifestyle_sents).strip()
    if not lifestyle_text:
        lifestyle_text = "Aim for regular physical activity and adequate sleep."
    return {
        "condition": ", ".join(sorted(diseases_found)),
        "allowed_foods": sorted(allowed),
        "restricted_foods": sorted(restricted),
        "diet_plan": diet_plan_text,
        "lifestyle_advice": lifestyle_text,
    }
