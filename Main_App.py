import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import re
import spacy

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Dummy_MyDiet_AI",
    page_icon="🍎",
    layout="centered"
)

st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(180deg, #f8fafc 0%, #ffffff 70%);}
    .app-header {padding: 20px 24px; border-radius: 14px; background:#0f172a; color:#fff; margin-bottom: 8px;}
    .app-header .brand {font-size: 24px; font-weight: 700; letter-spacing:.2px;}
    .app-header .subtitle {margin-top:6px; opacity:.85}
    .app-header .steps {display:flex; gap:10px; flex-wrap:wrap; margin-top:12px;}
    .app-header .step {background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.14); padding:8px 12px; border-radius:10px; font-size:14px;}
    .app-footer {margin-top:32px; padding:14px; border-top:1px solid #e5e7eb; color:#64748b; text-align:center; font-size:13px;}
    </style>
    <div class="app-header">
      <div class="brand">🍎 Dummy_MyDiet_AI</div>
      <div class="subtitle">AI-based Personalized Diet Recommendation System</div>
      <div class="steps">
        <div class="step">1. Upload report or CSV (doctor_prescription)</div>
        <div class="step">2. Set patient attributes</div>
        <div class="step">3. Generate and download diet plan</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# -------------------- LOAD NLP SAFELY --------------------
@st.cache_resource
def load_spacy():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp

nlp = load_spacy()

# -------------------- TEXT EXTRACTION (MILESTONE 1) --------------------
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


# -------------------- NLP + DIET LOGIC (MILESTONE 3) --------------------
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

# -------------------- USER INPUT UI --------------------
st.subheader("📄 Upload Medical Report")

uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

st.subheader("👤 Patient Attributes")
col1, col2, col3 = st.columns(3)
with col1:
    gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"], index=0)
with col2:
    activity_level = st.selectbox("Activity Level", ["Select", "Sedentary", "Low", "Moderate", "Active", "High"], index=0)
with col3:
    diabetes = st.selectbox("Diabetes", ["No", "Yes", "Type 1", "Type 2"])

col4, col5, col6 = st.columns(3)
with col4:
    high_cholesterol = st.selectbox("High Cholesterol", ["No", "Yes"])
with col5:
    bmi = st.number_input("BMI", min_value=10.0, max_value=60.0, value=24.0, step=0.1)
with col6:
    total_cholesterol = st.number_input("Total Cholesterol (mg/dL)", min_value=100.0, max_value=400.0, value=180.0, step=1.0)

col7, col8 = st.columns(2)
with col7:
    glucose = st.number_input("Glucose (mg/dL)", min_value=50.0, max_value=300.0, value=100.0, step=1.0)
with col8:
    diet_type = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])

intolerances = st.multiselect("Intolerances", ["Lactose", "Gluten", "Nuts", "Soy", "Eggs", "Shellfish"])

exp = st.expander("Doctor's Prescription (optional)")
with exp:
    manual_text = st.text_area("Paste doctor prescription text here", height=150)

st.divider()

process_btn = st.button("🔍 Generate Diet Recommendation")

# -------------------- PIPELINE EXECUTION --------------------
if process_btn:
    st.success("✅ Processing input...")

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

    st.subheader("📝 Extracted Text")
    st.write(text[:1000])

    st.subheader("🩺 Health Status")
    st.info("Health condition inferred using medical text analysis.")

    diet = generate_diet(text)

    st.subheader("🍽️ Personalized Diet Recommendation")
    st.json(diet)

    st.download_button(
        label="⬇️ Download Diet Plan (JSON)",
        data=pd.Series(diet).to_json(),
        file_name="diet_plan.json",
        mime="application/json"
    )

st.markdown(
    """
    <div class="app-footer">
      Built for demos and testing. Upload a doctor report or CSV with a doctor_prescription column to get a quick diet plan suggestion.
    </div>
    """,
    unsafe_allow_html=True,
)
