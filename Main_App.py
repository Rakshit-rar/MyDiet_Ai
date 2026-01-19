import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import re
import spacy

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="MyDiet_AI",
    page_icon="🍎",
    layout="centered"
)

# -------------------- HERO SECTION --------------------
st.markdown(
    """
    <div style="text-align:center; padding: 1.5rem 0;">
        <h1>🍎 MyDiet_AI</h1>
        <p style="font-size:1.05rem; opacity:0.85;">
            AI-based Personalized Diet Recommendation System
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

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
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    elif ext in ["png", "jpg", "jpeg"]:
        try:
            img = Image.open(uploaded_file)
            text = pytesseract.image_to_string(img)
        except Exception:
            text = (
                "⚠️ Image OCR is not supported in this deployment environment.\n"
                "Please upload PDF / TXT / CSV files or paste text manually."
            )

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        if "doctor_prescription" in df.columns:
            text = df["doctor_prescription"].iloc[0]
        else:
            text = "⚠️ CSV file does not contain 'doctor_prescription' column."

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
        diet["diet_plan"].append("Follow a diabetic-friendly low sugar diet.")
        diet["lifestyle_advice"].append("Walk daily for 30 minutes.")

    if "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted_foods"].append("oily food")
        diet["diet_plan"].append("Increase fiber intake and avoid fried foods.")

    if "blood pressure" in text or "hypertension" in text:
        diet["condition"].append("Hypertension")
        diet["restricted_foods"].append("salt")
        diet["diet_plan"].append("Reduce sodium intake.")
        diet["lifestyle_advice"].append("Practice stress management.")

    if not diet["condition"]:
        diet["condition"].append("General Health")
        diet["diet_plan"].append("Maintain a balanced diet.")
        diet["lifestyle_advice"].append("Stay active and hydrated.")

    return {
        "condition": ", ".join(diet["condition"]),
        "allowed_foods": list(set(diet["allowed_foods"])),
        "restricted_foods": list(set(diet["restricted_foods"])),
        "diet_plan": " ".join(diet["diet_plan"]),
        "lifestyle_advice": " ".join(diet["lifestyle_advice"])
    }

# -------------------- INPUT SECTION --------------------
st.subheader("📄 Medical Report")
uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

st.subheader("👤 Patient Information")

col1, col2, col3 = st.columns(3)
with col1:
    gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"])
with col2:
    activity_level = st.selectbox("Activity Level", ["Select", "Sedentary", "Low", "Moderate", "Active", "High"])
with col3:
    diabetes = st.selectbox("Diabetes", ["No", "Yes", "Type 1", "Type 2"])

col4, col5, col6 = st.columns(3)
with col4:
    high_cholesterol = st.selectbox("High Cholesterol", ["No", "Yes"])
with col5:
    bmi = st.number_input("BMI", 10.0, 60.0, 24.0, 0.1)
with col6:
    total_cholesterol = st.number_input("Total Cholesterol (mg/dL)", 100.0, 400.0, 180.0)

col7, col8 = st.columns(2)
with col7:
    glucose = st.number_input("Glucose (mg/dL)", 50.0, 300.0, 100.0)
with col8:
    diet_type = st.selectbox("Diet Preference", ["Vegetarian", "Non-Vegetarian", "Vegan"])

intolerances = st.multiselect(
    "Food Intolerances",
    ["Lactose", "Gluten", "Nuts", "Soy", "Eggs", "Shellfish"]
)

with st.expander("📝 Doctor’s Prescription (Optional)"):
    manual_text = st.text_area(
        "Paste prescription text",
        height=140
    )

st.markdown("---")

process_btn = st.button("🔍 Generate Personalized Diet", use_container_width=True)

# -------------------- OUTPUT SECTION --------------------
if process_btn:
    st.success("Processing patient data...")

    if uploaded_file:
        text = extract_text(uploaded_file)
    else:
        text = manual_text.strip()

    tokens = []
    if diabetes != "No":
        tokens.append("diabetes")
    if high_cholesterol == "Yes" or total_cholesterol >= 200:
        tokens.append("cholesterol")

    if text.strip() == "" and tokens:
        text = " ".join(tokens)

    st.subheader("📝 Extracted Medical Text")
    st.write(text[:1000] if text else "No text provided.")

    st.subheader("🩺 Health Analysis")
    st.info("Health conditions inferred using medical text and patient inputs.")

    diet = generate_diet(text)

    st.subheader("🍽️ Diet Recommendation")
    st.json(diet)

    st.download_button(
        "⬇️ Download Diet Plan (JSON)",
        data=pd.Series(diet).to_json(),
        file_name="diet_plan.json",
        mime="application/json",
        use_container_width=True
    )
