import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import spacy

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="MyDiet_AI | Clinical Diet Engine",
    page_icon="🥗",
    layout="wide"
)

# -------------------- HEADER --------------------
st.markdown("""
## 🧠 MyDiet_AI – Clinical Diet Recommendation Engine
A rule-based AI system that analyzes **medical reports & patient attributes**
to generate **personalized diet and meal plans**.
""")
st.markdown("---")

# -------------------- LOAD NLP --------------------
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
        except Exception:
            text = "OCR not supported in this environment."

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        if "doctor_prescription" in df.columns:
            text = df["doctor_prescription"].iloc[0]

    return text.strip()

# -------------------- DIET LOGIC --------------------
def generate_diet(text):
    diet = {
        "condition": [],
        "allowed_foods": ["vegetables", "whole grains", "fruits"],
        "restricted_foods": [],
        "diet_plan": [],
        "lifestyle_advice": []
    }

    text = text.lower()

    if "diabetes" in text:
        diet["condition"].append("Diabetes")
        diet["restricted_foods"].append("sugar")
        diet["diet_plan"].append("Low sugar, low GI diet.")
        diet["lifestyle_advice"].append("Daily walking recommended.")

    if "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted_foods"].append("fried food")
        diet["diet_plan"].append("Increase fiber intake.")

    if "blood pressure" in text or "hypertension" in text:
        diet["condition"].append("Hypertension")
        diet["restricted_foods"].append("salt")
        diet["diet_plan"].append("Low sodium diet.")

    if not diet["condition"]:
        diet["condition"].append("General Health")
        diet["diet_plan"].append("Balanced nutrition advised.")
        diet["lifestyle_advice"].append("Stay active and hydrated.")

    return {
        "condition": ", ".join(diet["condition"]),
        "allowed_foods": list(set(diet["allowed_foods"])),
        "restricted_foods": list(set(diet["restricted_foods"])),
        "diet_plan": " ".join(diet["diet_plan"]),
        "lifestyle_advice": " ".join(diet["lifestyle_advice"])
    }

def generate_meal_plan(has_diabetes, has_cholesterol, diet_type):
    veg = diet_type in ["Vegetarian", "Vegan"]
    dairy = diet_type != "Vegan"

    plan = [
        {
            "breakfast": "Oats with milk" if dairy else "Oats with soy milk",
            "lunch": "Grilled chicken salad" if not veg else "Quinoa & legumes",
            "snack": "Fruits & nuts",
            "dinner": "Steamed fish & vegetables" if not veg else "Tofu & vegetables"
        },
        {
            "breakfast": "Vegetable smoothie",
            "lunch": "Brown rice & curry",
            "snack": "Yogurt & berries" if dairy else "Berries & nuts",
            "dinner": "Grilled chicken" if not veg else "Grilled tofu"
        }
    ]
    return plan

def meal_plan_text(plan):
    out = []
    for i, d in enumerate(plan, 1):
        out.append(f"Day {i}")
        for k, v in d.items():
            out.append(f"{k.title()}: {v}")
        out.append("")
    return "\n".join(out)

# ====================== SIDEBAR INPUT ======================
st.sidebar.title("🧾 Patient Input Panel")
st.sidebar.caption("Medical data & lifestyle attributes")

uploaded_file = st.sidebar.file_uploader(
    "Upload Medical Report",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

with st.sidebar.expander("Doctor's Prescription (Optional)"):
    manual_text = st.text_area("Paste prescription text", height=120)

gender = st.sidebar.selectbox("Gender", ["Select", "Male", "Female", "Other"])
activity = st.sidebar.selectbox("Activity Level", ["Select", "Sedentary", "Low", "Moderate", "Active"])
diabetes = st.sidebar.selectbox("Diabetes", ["No", "Yes", "Type 1", "Type 2"])
chol = st.sidebar.selectbox("High Cholesterol", ["No", "Yes"])

bmi = st.sidebar.number_input("BMI", 10.0, 60.0, 24.0)
chol_val = st.sidebar.number_input("Total Cholesterol", 100.0, 400.0, 180.0)
glucose = st.sidebar.number_input("Glucose", 50.0, 300.0, 100.0)

diet_type = st.sidebar.selectbox("Diet Preference", ["Vegetarian", "Non-Vegetarian", "Vegan"])
intolerances = st.sidebar.multiselect("Food Intolerances", ["Lactose", "Gluten", "Nuts", "Soy"])

process_btn = st.sidebar.button("🔍 Generate Diet Plan")

# ====================== OUTPUT ======================
if process_btn:
    st.success("Processing patient data...")

    if uploaded_file:
        text = extract_text(uploaded_file)
    else:
        text = manual_text

    tokens = []
    if diabetes != "No":
        tokens.append("diabetes")
    if chol == "Yes" or chol_val >= 200:
        tokens.append("cholesterol")

    if not text and tokens:
        text = " ".join(tokens)

    st.markdown("### 📝 Extracted Clinical Text")
    st.write(text[:1000] if text else "No clinical text provided.")

    diet = generate_diet(text)

    st.markdown("### 🍽️ Diet Recommendation Summary")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Health Condition", diet["condition"])
        st.write("**Allowed Foods**")
        st.write(", ".join(diet["allowed_foods"]))
    with c2:
        st.write("**Restricted Foods**")
        st.write(", ".join(diet["restricted_foods"]))

    st.info(diet["diet_plan"])
    st.success(diet["lifestyle_advice"])

    mp = generate_meal_plan(diabetes != "No", chol == "Yes", diet_type)

    st.markdown("### 📅 Meal Plan Schedule")
    for i, day in enumerate(mp, 1):
        with st.expander(f"Day {i}"):
            for k, v in day.items():
                st.write(f"**{k.title()}**: {v}")

    st.download_button(
        "⬇️ Download Diet Plan (JSON)",
        data=pd.Series(diet).to_json(),
        file_name="diet_plan.json"
    )

    st.download_button(
        "⬇️ Download Meal Plan (TXT)",
        data=meal_plan_text(mp),
        file_name="meal_plan.txt"
    )
