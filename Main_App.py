import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import spacy

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="MyDiet",
    page_icon="🥗",
    layout="wide"
)

# ================= LIGHT THEME STYLES =================
st.markdown(
    """
    <style>
    .main {background-color:#f8fafc;}
    h1, h2, h3 {color:#0f172a;}
    .card {
        background:#ffffff;
        padding:24px;
        border-radius:18px;
        box-shadow:0 8px 24px rgba(15,23,42,0.08);
        margin-bottom:24px;
        border:1px solid #e5e7eb;
    }
    .accent {
        background:linear-gradient(90deg,#22c55e,#3b82f6);
        padding:12px 20px;
        border-radius:12px;
        color:white;
        font-weight:600;
        text-align:center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ================= HEADER =================
col1, col2 = st.columns([1,5])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2927/2927347.png", width=70)
with col2:
    st.markdown("## MyDiet")
    st.caption("Personalized Nutrition & Diet Recommendation System")

st.markdown("---")

# ================= NLP =================
@st.cache_resource
def load_spacy():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp

nlp = load_spacy()

# ================= TEXT EXTRACTION =================
def extract_text(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()
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
            text = "OCR not supported in this environment"

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        text = df.iloc[0].astype(str).str.cat(sep=" ")

    return text

# ================= DIET ENGINE =================
def generate_diet(text):
    text = text.lower()
    diet = {
        "condition": "General Wellness",
        "allowed_foods": ["vegetables", "fruits", "whole grains"],
        "restricted_foods": [],
        "recommendation": "Maintain balanced meals and daily activity"
    }

    if "diabetes" in text:
        diet.update({
            "condition": "Diabetes",
            "restricted_foods": ["sugar", "refined carbs"],
            "recommendation": "Low‑GI diet with controlled carbohydrates"
        })

    if "cholesterol" in text:
        diet["restricted_foods"].append("fried foods")

    if "hypertension" in text or "blood pressure" in text:
        diet["restricted_foods"].append("excess salt")

    return diet

# ================= UI LAYOUT =================
st.markdown('<div class="accent">Upload your medical report to receive a personalized diet plan</div>', unsafe_allow_html=True)

left, right = st.columns([2,3])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📄 Medical Report Input")
    uploaded_file = st.file_uploader("Upload PDF / Image / TXT / CSV", type=["pdf","png","jpg","jpeg","txt","csv"])
    manual_text = st.text_area("Or paste medical / prescription text", height=160)
    run = st.button("🍽️ Generate Diet Plan")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Diet Recommendation Output")
    if run:
        text = extract_text(uploaded_file) if uploaded_file else manual_text
        diet = generate_diet(text)
        st.json(diet)
        st.download_button("⬇️ Download as JSON", pd.Series(diet).to_json(), "diet_plan.json")
    else:
        st.info("Results will appear here after analysis")
    st.markdown('</div>', unsafe_allow_html=True)
