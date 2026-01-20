import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import io
import re

def _ocr_space_fallback(image):
    try:
        import requests
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        files = {"file": ("image.png", buf.getvalue(), "image/png")}
        data = {"apikey": "helloworld", "language": "eng", "isOverlayRequired": False}
        r = requests.post("https://api.ocr.space/parse/image", files=files, data=data, timeout=20)
        if r.status_code == 200:
            j = r.json()
            if j.get("ParsedResults"):
                return j["ParsedResults"][0].get("ParsedText", "").strip()
        return ""
    except Exception:
        return ""

def _parse_numeric(text):
    out = {}
    lower = text.lower()
    m = re.search(r"\bage\s*[:\-]?\s*(\d{1,3})\b", lower)
    if m:
        out["age"] = float(m.group(1))
    m = re.search(r"\bheight\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*cm\b", lower)
    if m:
        out["height_cm"] = float(m.group(1))
    m = re.search(r"\bheight\s*[:\-]?\s*(\d(?:\.\d+)?)\s*m\b", lower)
    if m and "height_cm" not in out:
        out["height_cm"] = float(m.group(1)) * 100.0
    m = re.search(r"\bweight\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*kg\b", lower)
    if m:
        out["weight_kg"] = float(m.group(1))
    m = re.search(r"\bbmi\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)\b", lower)
    if m:
        out["bmi"] = float(m.group(1))
    m = re.search(r"\b(fasting\s+glucose|glucose)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\b", lower)
    if m:
        out["glucose"] = float(m.group(2))
    m = re.search(r"\b(total\s*cholesterol|cholesterol)\s*[:\-]?\s*(\d{3}(?:\.\d+)?)\b", lower)
    if m:
        out["cholesterol"] = float(m.group(2))
    m = re.search(r"\bldl\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\b", lower)
    if m:
        out["ldl"] = float(m.group(1))
    m = re.search(r"\bhdl\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\b", lower)
    if m:
        out["hdl"] = float(m.group(1))
    m = re.search(r"\btriglycerides?\s*[:\-]?\s*(\d{2,4}(?:\.\d+)?)\b", lower)
    if m:
        out["triglycerides"] = float(m.group(1))
    m = re.search(r"\b(blood\s*pressure|bp)\s*[:\-]?\s*(\d{2,3})\s*/\s*(\d{2,3})\b", lower)
    if m:
        out["bp_systolic"] = float(m.group(2))
        out["bp_diastolic"] = float(m.group(3))
        out["blood_pressure"] = float(m.group(2))
    if ("bmi" not in out) and ("height_cm" in out) and ("weight_kg" in out):
        h_m = out["height_cm"] / 100.0
        if h_m > 0:
            out["bmi"] = round(out["weight_kg"] / (h_m * h_m), 2)
    return out if out else None

def extract_text(uploaded_file):
    text = ""
    numeric_data = None
    file_type = uploaded_file.name.split(".")[-1].lower()
    if file_type == "pdf":
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                numeric_data = _parse_numeric(text)
            else:
                text = "⚠️ PDF appears to be image-only or text extraction failed.\nPlease upload TXT/CSV or paste text manually."
        except Exception:
            text = "⚠️ PDF reading failed in this environment.\nPlease upload TXT/CSV or paste text manually."
    elif file_type in ["png", "jpg", "jpeg"]:
        try:
            image = Image.open(uploaded_file)
            if image.mode != "L":
                image = image.convert("L")
            w, h = image.size
            if w < 1200:
                scale = 1200 / float(w)
                image = image.resize((int(w * scale), int(h * scale)))
            image = image.point(lambda p: 255 if p > 180 else 0)
            text = pytesseract.image_to_string(image, config="--psm 6")
            if not text.strip():
                alt_text = _ocr_space_fallback(image)
                text = alt_text or "⚠️ OCR produced empty text.\nPlease upload PDF/TXT/CSV or paste text manually."
            numeric_data = _parse_numeric(text) if text and text.strip() else None
        except Exception:
            try:
                image = Image.open(uploaded_file)
                alt_text = _ocr_space_fallback(image)
                text = alt_text or "⚠️ Image OCR is not supported in this deployment environment.\nPlease upload PDF/TXT/CSV files or paste text manually."
                numeric_data = _parse_numeric(text) if text and text.strip() else None
            except Exception:
                text = "⚠️ Image OCR is not supported in this deployment environment.\nPlease upload PDF/TXT/CSV files or paste text manually."
                numeric_data = None
    elif file_type == "txt":
        try:
            text = uploaded_file.read().decode("utf-8")
        except Exception:
            text = uploaded_file.read().decode(errors="ignore")
        numeric_data = _parse_numeric(text) if text and text.strip() else None
    elif file_type == "csv":
        df = pd.read_csv(uploaded_file)
        if "doctor_prescription" in df.columns:
            text = str(df["doctor_prescription"].iloc[0])
        else:
            text = "⚠️ CSV does not contain 'doctor_prescription' column."
        numeric_data = df.iloc[0].to_dict()
    return text, numeric_data
