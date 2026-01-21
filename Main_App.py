import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import re
import spacy
import json
import random
from Utilities.diet_extractor import extract_text as util_extract_text
from Utilities.diet_generator import generate_diet as util_generate_diet
def safe_predict_condition(numeric_data):
    try:
        import pandas as pd
        from joblib import load
        from pathlib import Path
        model_path = Path(__file__).resolve().parent / "ML_model" / "ML_model.pkl"
        model = load(str(model_path))
        features = ["age", "glucose", "cholesterol", "blood_pressure", "bmi"]
        X = pd.DataFrame([[numeric_data[f] for f in features]], columns=features)
        pred = model.predict(X)[0]
        return "Abnormal" if int(pred) == 1 else "Normal"
    except Exception:
        gl = numeric_data.get("glucose")
        chol = numeric_data.get("cholesterol")
        bp = numeric_data.get("blood_pressure")
        bmi = numeric_data.get("bmi")
        flags = 0
        if gl is not None and gl >= 126:
            flags += 1
        if chol is not None and chol >= 240:
            flags += 1
        if bp is not None and bp >= 140:
            flags += 1
        if bmi is not None and bmi >= 30:
            flags += 1
        return "Abnormal" if flags >= 1 else "Normal"

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="MyDiet_AI",
    page_icon="🍎",
    layout="wide"
)

# -------------------- CUSTOM CSS & STYLING --------------------
st.markdown("""
<style>
    /* Global Settings */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* Header Styling */
    .main-header {
        background: linear-gradient(90deg, #FF4B2B 0%, #FF416C 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    .main-header h1 {
        color: white !important;
        font-weight: 700;
        font-size: 3.5rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.95;
        margin-top: 1rem;
        font-weight: 300;
    }

    /* Cards/Containers */
    .css-1r6slb0, .css-12oz5g7 {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(56, 239, 125, 0.5);
    }
    
    /* Typography */
    h2 {
        color: #2c3e50;
        font-weight: 600;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #38ef7d;
        padding-bottom: 0.5rem;
        display: inline-block;
    }
    h3 {
        color: #34495e;
        margin-top: 1.5rem;
    }
    
    /* Result Cards */
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border-left: 5px solid #38ef7d;
    }
    
</style>
""", unsafe_allow_html=True)

# -------------------- HERO SECTION --------------------
st.markdown("""
<div class="main-header">
    <h1>🍎 MyDiet_AI</h1>
    <p>Your Personalized AI Nutritionist & Diet Planner</p>
</div>
""", unsafe_allow_html=True)

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
    def nv(nonveg_item, veg_item):
        return nonveg_item if not veg else veg_item
    def dairy(with_dairy_item, no_dairy_item):
        return with_dairy_item if dairy_ok else no_dairy_item
    def build_week(menu):
        b = menu["breakfast"][:]
        l = menu["lunch"][:]
        s = menu["snack"][:]
        d = menu["dinner"][:]
        random.shuffle(b)
        random.shuffle(l)
        random.shuffle(s)
        random.shuffle(d)
        days = []
        for i in range(7):
            days.append({
                "breakfast": b[i % len(b)],
                "lunch": l[i % len(l)],
                "snack": s[i % len(s)],
                "dinner": d[i % len(d)],
            })
        return days
    group = "both" if has_diabetes and has_high_cholesterol else ("diabetes" if has_diabetes else ("cholesterol" if has_high_cholesterol else "general"))
    dia_alt1 = {
        "breakfast": [
            dairy("Oats porridge with skim milk, green tea", "Oats porridge with soy milk, green tea"),
            "Moong dal chilla with mint chutney",
            "Ragi dosa with sambar",
            "Vegetable upma",
            "Poha with vegetables",
            dairy("Dalia with milk and nuts", "Dalia with soy milk and nuts"),
        ],
        "lunch": [
            "Whole wheat roti, dal, mixed sabzi",
            "Brown rice, rajma, salad",
            nv("Grilled chicken salad with olive oil and lemon", "Quinoa salad with legumes"),
            nv("Fish curry with brown rice", "Millet khichdi, salad"),
            dairy("Curd rice with cucumber", "Quinoa pulao, cucumber salad"),
        ],
        "snack": [
            "Sprouts chaat",
            "Roasted chana and walnuts",
            dairy("Unsweetened yogurt with chia", "Soy yogurt with chia"),
            "Apple or guava slices",
            "Carrot sticks with hummus",
        ],
        "dinner": [
            nv("Grilled fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
            "Dal, roti, sautéed greens",
            dairy("Paneer bhurji with roti", "Tofu bhurji with roti"),
            "Vegetable curry with cauliflower rice",
            "Khichdi with cucumber salad",
        ],
    }
    dia_alt2 = {
        "breakfast": [
            "Besan chilla, herbal tea",
            dairy("Greek yogurt with chia and berries", "Soy yogurt with chia and berries"),
            "Idli with sambar",
            "Vegetable dalia",
            "Ragi idli with sambar",
        ],
        "lunch": [
            "Brown rice, chole, salad",
            "Whole wheat roti, dal, bhindi/leafy greens",
            nv("Tandoori chicken with salad", "Paneer tikka with salad") if dairy_ok else "Tofu tikka with salad",
            "Millet khichdi, salad",
        ],
        "snack": [
            "Roasted peanuts (small portion) and fruit",
            "Sprouted moong salad",
            dairy("Buttermilk (unsweetened)", "Coconut water"),
            "Tomato-cucumber salad",
        ],
        "dinner": [
            nv("Grilled chicken with steamed broccoli", "Stir-fry tofu with vegetables"),
            "Dal, roti, sautéed greens",
            "Vegetable soup and salad",
            "Quinoa vegetable bowl",
        ],
    }
    dia_alt3 = {
        "breakfast": [
            "Oats upma, herbal tea",
            "Ragi dosa, sambar",
            "Poha with peanuts (low oil)",
            dairy("Curd with flax seeds", "Soy yogurt with flax seeds"),
        ],
        "lunch": [
            "Brown rice, sambar, salad",
            "Roti, dal, mixed veg",
            nv("Fish tikka with salad", "Grilled tofu with salad"),
            "Quinoa pulao, salad",
        ],
        "snack": [
            "Roasted chana",
            "Apple slices, almonds",
            "Carrot sticks, hummus",
            dairy("Lassi (unsweetened, low-fat)", "Unsweetened soy milk"),
        ],
        "dinner": [
            "Khichdi with salad",
            nv("Grilled fish with vegetables", "Paneer/tofu curry with roti") if dairy_ok else "Tofu curry with roti",
            "Vegetable curry with cauliflower rice",
            "Dal, roti, sautéed greens",
        ],
    }
    chol_alt1 = {
        "breakfast": [
            "Oats upma, herbal tea",
            "Ragi idli with sambar",
            "Vegetable poha with peanuts",
            dairy("Greek yogurt with chia and berries", "Soy yogurt with chia and berries"),
            "Multigrain toast with tomato chutney",
            "Fruit bowl and soaked almonds",
        ],
        "lunch": [
            "Brown rice, chole, salad",
            "Whole wheat roti, dal, mixed sabzi",
            "Millet khichdi, salad",
            nv("Grilled fish with lemon, salad", "Grilled tofu with lemon, salad"),
            "Mixed bean salad with olive oil and lemon",
            dairy("Vegetable daliya with curd", "Vegetable daliya with cucumber salad"),
        ],
        "snack": [
            "Roasted chana",
            "Sprouts chaat",
            "Carrot and cucumber sticks with hummus",
            "Apple slices and walnuts",
            dairy("Buttermilk (low-fat, unsalted)", "Coconut water"),
        ],
        "dinner": [
            "Dal, roti, sautéed greens",
            "Vegetable soup and salad",
            nv("Grilled chicken breast with vegetables", "Stir-fry vegetables with tofu"),
            "Khichdi with salad",
            "Quinoa vegetable salad",
        ],
    }
    chol_alt2 = {
        "breakfast": [
            "Masala oats, green tea",
            "Vegetable dalia",
            "Upma with vegetables",
            dairy("Curd with chia seeds", "Soy yogurt with chia seeds"),
        ],
        "lunch": [
            "Brown rice, rajma, salad",
            "Roti, dal, bhindi/leafy greens",
            nv("Fish curry with salad", "Tofu curry with salad"),
            "Quinoa pulao, salad",
        ],
        "snack": [
            "Roasted almonds (small portion) and fruit",
            "Sprouted moong salad",
            "Tomato-cucumber salad",
            dairy("Buttermilk (low-fat)", "Coconut water"),
        ],
        "dinner": [
            "Vegetable soup and salad",
            "Dal, roti, sautéed greens",
            nv("Grilled chicken tikka with vegetables", "Grilled tofu with vegetables"),
            "Millet khichdi, salad",
        ],
    }
    chol_alt3 = {
        "breakfast": [
            "Oats porridge with nuts",
            "Ragi dosa, sambar",
            "Poha (low oil) and herbal tea",
            "Multigrain porridge with seeds",
        ],
        "lunch": [
            "Brown rice, sambar, salad",
            "Roti, chole, mixed veg",
            "Quinoa salad with lemon dressing",
            nv("Grilled fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
        ],
        "snack": [
            "Roasted chana and walnuts",
            "Carrot sticks, hummus",
            "Apple or guava slices",
            dairy("Low-fat curd", "Soy yogurt"),
        ],
        "dinner": [
            "Khichdi with salad",
            "Dal, roti, sautéed greens",
            "Vegetable curry with cauliflower rice",
            "Mixed bean salad",
        ],
    }
    both_alt1 = {
        "breakfast": [
            "Besan chilla with mint chutney",
            "Oats upma, herbal tea",
            "Ragi dosa with sambar",
            "Vegetable dalia",
            "Idli with sambar",
        ],
        "lunch": [
            "Roti, dal, mixed veg (low oil)",
            "Brown rice, sambar, salad",
            "Millet khichdi, salad",
            nv("Grilled fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
            "Quinoa veggie bowl",
        ],
        "snack": [
            "Sprouts salad",
            "Roasted chana",
            "Apple or guava slices",
            dairy("Unsweetened curd with chia", "Soy yogurt with chia"),
            "Tomato-cucumber salad",
        ],
        "dinner": [
            "Dal, roti, sautéed greens",
            "Vegetable curry with cauliflower rice",
            "Tofu stir-fry with vegetables",
            "Khichdi with salad",
            nv("Grilled chicken/fish with vegetables", "Grilled tofu with vegetables"),
        ],
    }
    both_alt2 = {
        "breakfast": [
            "Ragi idli, sambar",
            dairy("Greek yogurt with berries", "Soy yogurt with berries"),
            "Multigrain porridge with seeds",
            "Upma with vegetables",
        ],
        "lunch": [
            "Roti, dal, greens",
            "Brown rice, rajma, salad",
            "Millet khichdi, salad",
            nv("Fish tikka with salad", "Paneer/tofu tikka with salad") if dairy_ok else "Tofu tikka with salad",
        ],
        "snack": [
            "Roasted peanuts (small portion) and fruit",
            "Sprouted moong chaat",
            "Carrot sticks, hummus",
            dairy("Buttermilk (unsweetened)", "Coconut water"),
        ],
        "dinner": [
            "Vegetable soup and salad",
            "Dal, roti, sautéed greens",
            "Quinoa vegetable bowl",
            nv("Grilled chicken breast with vegetables", "Stir-fry tofu with vegetables"),
        ],
    }
    both_alt3 = {
        "breakfast": [
            "Oats porridge, green tea",
            "Besan chilla",
            "Vegetable dalia",
            "Poha (low oil)",
        ],
        "lunch": [
            "Brown rice, sambar, salad",
            "Roti, chole, mixed veg",
            "Quinoa salad with lemon dressing",
            nv("Grilled fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
        ],
        "snack": [
            "Roasted chana",
            "Apple slices and walnuts",
            dairy("Low-fat curd with chia", "Soy yogurt with chia"),
            "Tomato-cucumber salad",
        ],
        "dinner": [
            "Khichdi with salad",
            "Dal, roti, sautéed greens",
            "Vegetable curry with cauliflower rice",
            nv("Grilled chicken/fish with vegetables", "Grilled tofu with vegetables"),
        ],
    }
    gen_alt = {
        "breakfast": [
            dairy("Oatmeal with skim milk, green tea", "Oatmeal with soy milk, green tea"),
            "Vegetable smoothie and whole grain toast",
            "Idli with sambar, herbal tea",
            "Upma with vegetables, green tea",
        ],
        "lunch": [
            nv("Grilled chicken salad with olive oil and lemon", "Quinoa salad with legumes"),
            "Dal, brown rice, mixed vegetables",
            "Chickpea salad wrap with lettuce and tomato",
        ],
        "snack": [
            "Apple slices, almonds",
            dairy("Low-fat yogurt, berries", "Berries with nuts"),
            "Carrot sticks, hummus",
            "Roasted chana, walnuts",
        ],
        "dinner": [
            nv("Steamed fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
            "Vegetable curry with cauliflower rice",
            "Lentil soup with whole grain bread",
            "Whole wheat roti with dal and sautéed greens",
        ],
    }
    if group == "diabetes":
        return build_week(random.choice([dia_alt1, dia_alt2, dia_alt3]))
    if group == "cholesterol":
        return build_week(random.choice([chol_alt1, chol_alt2, chol_alt3]))
    if group == "both":
        return build_week(random.choice([both_alt1, both_alt2, both_alt3]))
    return build_week(gen_alt)

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
    max_chars = 90
    try:
        tmp = Image.new("RGB", (width, height), "white")
        draw_tmp = ImageDraw.Draw(tmp)
        bbox = draw_tmp.textbbox((0, 0), "A", font=font)
        line_height = (bbox[3] - bbox[1]) + 6
    except Exception:
        tmp = Image.new("RGB", (width, height), "white")
        draw_tmp = ImageDraw.Draw(tmp)
        w, h = draw_tmp.textsize("A", font=font)
        line_height = h + 6
    lines = []
    for para in txt.split("\n"):
        wrapped = textwrap.wrap(para, width=max_chars) if para else [""]
        lines.extend(wrapped + [""])
    pages = []
    y = margin
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    for line in lines:
        if y + line_height > height - margin:
            pages.append(img)
            img = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(img)
            y = margin
        draw.text((margin, y), line, fill="black", font=font)
        y += line_height
    pages.append(img)
    buf = io.BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
    return buf.getvalue()
def has_required_numeric_data(d):
    req = ["age", "glucose", "cholesterol", "blood_pressure", "bmi"]
    return d is not None and all(k in d and d[k] is not None for k in req)

# -------------------- USER INPUT UI --------------------
st.markdown("## 📋 Patient Data & Preferences")

input_container = st.container()
with input_container:
    col1, col2 = st.columns([1, 1.5], gap="large")
    
    with col1:
        st.markdown("### � Upload Medical Report")
        st.info("Supported formats: PDF, JPG, PNG, TXT, CSV")
        uploaded_file = st.file_uploader(
            "Upload your file here",
            type=["pdf", "png", "jpg", "jpeg", "txt", "csv"],
            label_visibility="collapsed"
        )
        
    with col2:
        st.markdown("### 📝 Manual Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"], index=0)
        with c2:
            activity_level = st.selectbox("Activity Level", ["Select", "Sedentary", "Low", "Moderate", "Active", "High"], index=0)
        with c3:
            diabetes = st.selectbox("Diabetes", ["No", "Yes", "Type 1", "Type 2"])
            
        c4, c5 = st.columns(2)
        with c4:
            bmi = st.number_input("BMI", min_value=10.0, max_value=60.0, value=24.0, step=0.1)
        with c5:
            total_cholesterol = st.number_input("Total Cholesterol (mg/dL)", min_value=100.0, max_value=400.0, value=180.0, step=1.0)
            
        c6, c7 = st.columns(2)
        with c6:
            glucose = st.number_input("Glucose (mg/dL)", min_value=50.0, max_value=300.0, value=100.0, step=1.0)
        with c7:
            diet_type = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
            
        intolerances = st.multiselect("Intolerances", ["Lactose", "Gluten", "Nuts", "Soy", "Eggs", "Shellfish"])
        
        with st.expander("➕ Doctor's Prescription (Optional)"):
            manual_text = st.text_area("Paste text here", height=100)

st.markdown("<br>", unsafe_allow_html=True)
process_btn = st.button("✨ Generate Personalized Diet Plan")

# -------------------- PIPELINE EXECUTION --------------------
if process_btn:
    with st.spinner("🔄 Analyzing your health profile..."):
        if uploaded_file:
            text, numeric_data = util_extract_text(uploaded_file)
        else:
            text = manual_text.strip()
            numeric_data = None

        tokens = []
        if diabetes != "No":
            tokens.append("diabetes")
        if total_cholesterol >= 200:
            tokens.append("cholesterol")
        if text.strip() == "" and tokens:
            text = " ".join(tokens)

        # Show extracted text preview in a cleaner way
        with st.expander("📝 View Extracted Text", expanded=False):
            st.write(text[:1000] if text else "No text extracted.")

        diet = util_generate_diet(text)
        ml_pred = None
        if has_required_numeric_data(numeric_data):
            ml_pred = safe_predict_condition(numeric_data)

    # Results Display
    st.markdown("---")
    st.markdown("## 🥗 Your Personalized Nutrition Plan")
    
    # Condition & Prediction Row
    st.markdown(f"""
    <div class="result-card">
        <h3>🩺 Health Analysis</h3>
        <p><strong>Detected Condition:</strong> <span style="color: #e74c3c; font-weight: bold;">{diet['condition']}</span></p>
        {f'<p><strong>ML Risk Assessment:</strong> <span style="color: #e67e22; font-weight: bold;">{ml_pred}</span></p>' if ml_pred else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Foods Row
    c_allow, c_restrict = st.columns(2)
    with c_allow:
        items = "".join([f"<li>{x}</li>" for x in diet["allowed_foods"]])
        st.markdown(f"""
        <div class="result-card" style="border-left: 5px solid #2ecc71;">
            <h3 style="color: #2ecc71;">✅ Foods to Include</h3>
            <ul style="padding-left: 20px;">{items}</ul>
        </div>
        """, unsafe_allow_html=True)
        
    with c_restrict:
        items = "".join([f"<li>{x}</li>" for x in diet["restricted_foods"]])
        st.markdown(f"""
        <div class="result-card" style="border-left: 5px solid #e74c3c;">
            <h3 style="color: #e74c3c;">❌ Foods to Avoid</h3>
            <ul style="padding-left: 20px;">{items}</ul>
        </div>
        """, unsafe_allow_html=True)

    # Advice
    st.markdown(f"""
    <div class="result-card" style="border-left: 5px solid #3498db;">
        <h3 style="color: #3498db;">💡 Lifestyle & Diet Advice</h3>
        <p><strong>Diet Strategy:</strong> {diet['diet_plan']}</p>
        <p><strong>Daily Habits:</strong> {diet['lifestyle_advice']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Meal Plan
    cond_text = diet["condition"].lower()
    has_d = ("diabetes" in cond_text) or (diabetes != "No")
    has_c = ("cholesterol" in cond_text) or (total_cholesterol >= 200)
    mp = generate_meal_plan(has_d, has_c, diet_type)
    
    st.markdown("## 📅 7-Day Meal Schedule")
    
    for idx, day in enumerate(mp, start=1):
        st.markdown(f"""
        <div class="result-card" style="border-left: 5px solid #FF416C; margin-bottom: 20px;">
            <h4 style="color: #2c3e50; margin-bottom: 1rem;">📅 Day {idx}</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px;">
                    <strong>🍳 Breakfast</strong><br>
                    <span style="color: #555;">{day['breakfast']}</span>
                </div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px;">
                    <strong>🍱 Lunch</strong><br>
                    <span style="color: #555;">{day['lunch']}</span>
                </div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px;">
                    <strong>🍎 Snack</strong><br>
                    <span style="color: #555;">{day['snack']}</span>
                </div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px;">
                    <strong>🍽️ Dinner</strong><br>
                    <span style="color: #555;">{day['dinner']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Downloads
    st.markdown("### 📥 Download Your Plan")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            label="📄 Download JSON",
            data=json.dumps({"diet": diet, "weekly_meal_plan": mp}, indent=2),
            file_name="diet_plan.json",
            mime="application/json"
        )
    with d2:
        st.download_button(
            label="📑 Download PDF",
            data=meal_plan_pdf(mp),
            file_name="meal_plan.pdf",
            mime="application/pdf"
        )
