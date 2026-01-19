def generate_diet(text):
    text = text.lower()

    diet = {
        "condition": "",
        "allowed_foods": ["vegetables", "whole grains", "fruits"],
        "restricted_foods": [],
        "diet_plan": "",
        "lifestyle_advice": ""
    }

    if "diabetes" in text:
        diet["condition"] += "Diabetes "
        diet["restricted_foods"].append("sugar")
        diet["diet_plan"] += "Follow diabetic diet. "
        diet["lifestyle_advice"] += "Walk daily. "

    if "cholesterol" in text:
        diet["condition"] += "Cholesterol "
        diet["restricted_foods"].append("oily food")

    if "blood pressure" in text or "hypertension" in text:
        diet["condition"] += "Hypertension "
        diet["restricted_foods"].append("salt")

    if diet["diet_plan"] == "":
        diet["diet_plan"] = "Maintain a balanced and healthy diet."

    return diet