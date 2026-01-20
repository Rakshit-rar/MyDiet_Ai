import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import spacy
import json

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="MyDiet_AI",
    page_icon="🍎",
    layout="centered"
)

st.title("🍎 MyDiet_AI")
st.caption("AI-based Personalized Diet Recommendation System")
st.markdown("---")

# -------------------- LOAD NLP SAFELY --------------------
@st.cache_resource
def load_spacy():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp

nlp = load_spacy()

# -------------------- TEXT EXTRACTION --------------------
def extract_text(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    text = ""

    if ext == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

    elif ext in ["png", "jpg", "jpeg"]:
        try:
            img = Image.open(uploaded_file)
            text = pytesseract.image_to_string(img)
        except:
            text = ""

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        if "doctor_prescription" in df.columns:
            text = df["doctor_prescription"].iloc[0]

    return text.strip()

# -------------------- DIET GENERATION (FIXED) --------------------
def generate_diet(text, bmi, glucose, cholesterol, activity_level, intolerances):
    diet = {
        "condition": [],
        "allowed_foods": [],
        "restricted_foods": [],
        "diet_plan": [],
        "lifestyle_advice": []
    }

    text = text.lower()

    if glucose >= 126 or "diabetes" in text:
        diet["condition"].append("Diabetes")
        diet["restricted_foods"].extend(["sugar", "sweetened drinks"])
        diet["diet_plan"].append("Low glycemic index diet.")
        diet["lifestyle_advice"].append("Daily walking for 30–45 minutes.")

    if cholesterol >= 200 or "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted_foods"].extend(["fried food", "trans fats"])
        diet["diet_plan"].append("High fiber, low-fat diet.")
        diet["lifestyle_advice"].append("Avoid packaged foods.")

    if "hypertension" in text or "blood pressure" in text:
        diet["condition"].append("Hypertension")
        diet["restricted_foods"].append("excess salt")
        diet["diet_plan"].append("Low sodium DASH diet.")
        diet["lifestyle_advice"].append("Stress control and adequate sleep.")

    if bmi >= 30:
        diet["condition"].append("Obesity")
        diet["diet_plan"].append("Calorie deficit diet for weight loss.")
        diet["lifestyle_advice"].append("Avoid late-night eating.")

    if not diet["condition"]:
        diet["condition"].append("General Health")
        diet["diet_plan"].append("Balanced diet with portion control.")
        diet["lifestyle_advice"].append("Stay active and hydrated.")

    diet["allowed_foods"] = [
        "vegetables", "whole grains", "lean protein", "fruits", "healthy fats"
    ]

    if "Lactose" in intolerances:
        diet["restricted_foods"].append("dairy products")
    if "Gluten" in intolerances:
        diet["restricted_foods"].append("gluten")

    return {
        "condition": ", ".join(set(diet["condition"])),
        "allowed_foods": list(set(diet["allowed_foods"])),
        "restricted_foods": list(set(diet["restricted_foods"])),
        "diet_plan": " ".join(diet["diet_plan"]),
        "lifestyle_advice": " ".join(diet["lifestyle_advice"])
    }

# -------------------- MEAL PLAN (FIXED) --------------------
def generate_meal_plan(has_diabetes, has_high_cholesterol, bmi, diet_type):
    veg = diet_type in ["Vegetarian", "Vegan"]
    dairy_ok = diet_type != "Vegan"
    portion = "small portions" if bmi >= 30 else "standard portions"

    return [
        {
            "breakfast": f"Oatmeal ({portion})",
            "lunch": "Quinoa salad" if veg else "Grilled chicken salad",
            "snack": "Apple with nuts",
            "dinner": "Grilled tofu with veggies" if veg else "Steamed fish with vegetables"
        }
        for _ in range(7)
    ]

# -------------------- PDF GENERATOR --------------------
def meal_plan_pdf(plan):
    font = ImageFont.load_default()
    width, height = 800, 1100
    margin = 40
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    y = margin

    for i, day in enumerate(plan, 1):
        text = f"Day {i}: {day}"
        draw.text((margin, y), text, fill="black", font=font)
        y += 30

    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()

# -------------------- UI --------------------
left, right = st.columns(2)

with left:
    uploaded_file = st.file_uploader("Upload Medical Report")

with right:
    bmi = st.number_input("BMI", 10.0, 60.0, 24.0)
    glucose = st.number_input("Glucose", 50.0, 300.0, 100.0)
    cholesterol = st.number_input("Cholesterol", 100.0, 400.0, 180.0)
    activity_level = st.selectbox("Activity Level", ["Low", "Moderate", "High"])
    diet_type = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
    intolerances = st.multiselect("Intolerances", ["Lactose", "Gluten", "Nuts"])
    manual_text = st.text_area("Doctor's Prescription")

if st.button("🔍 Generate Diet Plan"):
    text = extract_text(uploaded_file) if uploaded_file else manual_text

    diet = generate_diet(
        text, bmi, glucose, cholesterol, activity_level, intolerances
    )

    meal_plan = generate_meal_plan(
        glucose >= 126, cholesterol >= 200, bmi, diet_type
    )

    st.subheader("🍽️ Diet Summary")
    st.json(diet)

    st.subheader("📅 Weekly Meal Plan")
    st.json(meal_plan)

    st.download_button(
        "⬇️ Download JSON",
        json.dumps({"diet": diet, "meal_plan": meal_plan}, indent=2),
        "diet_plan.json"
    )

    st.download_button(
        "⬇️ Download PDF",
        meal_plan_pdf(meal_plan),
        "meal_plan.pdf",
        "application/pdf"
    )
