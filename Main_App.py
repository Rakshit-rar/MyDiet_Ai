import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import re
import spacy

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

def generate_meal_plan(has_diabetes, has_high_cholesterol, diet_type):
    veg = diet_type in ["Vegetarian", "Vegan"]
    dairy_ok = diet_type != "Vegan"
    b1 = "Oatmeal with skim milk" if dairy_ok else "Oatmeal with soy milk"
    t1 = "green tea"
    l1 = "Grilled chicken salad with olive oil dressing" if not veg else "Quinoa salad with legumes"
    s1 = "Apple slices, almonds"
    d1 = "Steamed fish with steamed vegetables" if not veg else "Grilled tofu with steamed vegetables"
    b2 = "Vegetable smoothie" + (" and whole grain toast" if not veg else " and whole grain toast")
    l2 = "Quinoa salad with legumes"
    s2 = ("Low-fat yogurt, berries" if dairy_ok else "Berries with nuts")
    d2 = "Grilled chicken with spinach" if not veg else "Grilled tofu with spinach"
    if has_diabetes:
        b1 = b1
        s1 = "Apple slices, almonds"
        s2 = s2
    if has_high_cholesterol:
        l1 = l1.replace("olive oil dressing", "olive oil and lemon")
        d1 = d1
    plan = [
        {"breakfast": f"{b1}, {t1}", "lunch": l1, "snack": s1, "dinner": d1},
        {"breakfast": b2, "lunch": l2, "snack": s2, "dinner": d2},
    ]
    return plan

def meal_plan_text(plan):
    lines = []
    for i, day in enumerate(plan, start=1):
        lines.append(f"Day {i}:")
        lines.append(f"Breakfast: {day['breakfast']}")
        lines.append(f"Lunch: {day['lunch']}")
        lines.append(f"Snack: {day['snack']}")
        lines.append(f"Dinner: {day['dinner']}")
        lines.append("")
    return "\n".join(lines).strip()
def meal_plan_pdf(plan):
    txt = meal_plan_text(plan)
    font = ImageFont.load_default()
    width, height = 800, 1100
    margin = 40
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    max_chars = 90
    y = margin
    line_height = font.getsize("A")[1] + 6
    for para in txt.split("\n"):
        wrapped = textwrap.wrap(para, width=max_chars) if para else [""]
        for line in wrapped:
            if y + line_height > height - margin:
                break
            draw.text((margin, y), line, fill="black", font=font)
            y += line_height
        y += 2
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()

# -------------------- USER INPUT UI --------------------
left_col, right_col = st.columns(2)
with left_col:
    st.subheader("📄 Upload Medical Report")
    uploaded_file = st.file_uploader(
        "Upload PDF / Image / TXT / CSV",
        type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
    )
with right_col:
    st.subheader("Manual Input & Attributes")
    col1, col2, col3 = st.columns(3)
    with col1:
        gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"], index=0)
    with col2:
        activity_level = st.selectbox("Activity Level", ["Select", "Sedentary", "Low", "Moderate", "Active", "High"], index=0)
    with col3:
        diabetes = st.selectbox("Diabetes", ["No", "Yes", "Type 1", "Type 2"])
    col4, col5 = st.columns(2)
    with col4:
        bmi = st.number_input("BMI", min_value=10.0, max_value=60.0, value=24.0, step=0.1)
    with col5:
        total_cholesterol = st.number_input("Total Cholesterol (mg/dL)", min_value=100.0, max_value=400.0, value=180.0, step=1.0)
    col6, col7 = st.columns(2)
    with col6:
        glucose = st.number_input("Glucose (mg/dL)", min_value=50.0, max_value=300.0, value=100.0, step=1.0)
    with col7:
        diet_type = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
    intolerances = st.multiselect("Intolerances", ["Lactose", "Gluten", "Nuts", "Soy", "Eggs", "Shellfish"])
    exp = st.expander("Doctor's Prescription (optional)")
    with exp:
        manual_text = st.text_area("Paste doctor prescription text here", height=150)

process_btn = st.button("🔍 Generate Diet plan")

# -------------------- PIPELINE EXECUTION --------------------
if process_btn:
    st.success("✅ Processing input file...")

    if uploaded_file:
        text = extract_text(uploaded_file)
    else:
        text = manual_text.strip()

    tokens = []
    if diabetes != "No":
        tokens.append("diabetes")
    if total_cholesterol >= 200:
        tokens.append("cholesterol")
    if text.strip() == "" and tokens:
        text = " ".join(tokens)

    st.subheader("📝 Extracted Text")
    st.write(text[:1000])
    
    diet = generate_diet(text)

    st.subheader("🍽️ Personalized Diet plan")
    st.write(f"Condition: {diet['condition']}")
    st.markdown("Allowed Foods:")
    for item in diet["allowed_foods"]:
        st.markdown(f"- {item}")
    st.markdown("Restricted Foods:")
    for item in diet["restricted_foods"]:
        st.markdown(f"- {item}")
    st.markdown("Diet Plan:")
    st.write(diet["diet_plan"])
    st.markdown("Lifestyle Advice:")
    st.write(diet["lifestyle_advice"])

    mp = generate_meal_plan(diabetes != "No", total_cholesterol >= 200, diet_type)
    st.subheader("📅 Daily Meal Plan")
    for idx, day in enumerate(mp, start=1):
        st.markdown(f"**Day {idx}**")
        st.write(f"Breakfast: {day['breakfast']}")
        st.write(f"Lunch: {day['lunch']}")
        st.write(f"Snack: {day['snack']}")
        st.write(f"Dinner: {day['dinner']}")

    st.download_button(
        label="⬇️ Download Diet Plan (JSON)",
        data=pd.Series(diet).to_json(),
        file_name="diet_plan.json",
        mime="application/json"
    )
    st.download_button(
        label="⬇️ Download Meal Plan (PDF)",
        data=meal_plan_pdf(mp),
        file_name="meal_plan.pdf",
        mime="application/pdf"
    )
