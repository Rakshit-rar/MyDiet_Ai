import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import io
import base64

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
            if not text.strip():
                text = (
                    "⚠️ PDF appears to be image-only or text extraction failed.\n"
                    "Please upload TXT/CSV or paste text manually."
                )
        except Exception:
            text = (
                "⚠️ PDF reading failed in this environment.\n"
                "Please upload TXT/CSV or paste text manually."
            )

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
                if alt_text:
                    text = alt_text
                else:
                    text = (
                        "⚠️ OCR produced empty text.\n"
                        "Please upload PDF/TXT/CSV or paste text manually."
                    )
        except Exception:
            try:
                image = Image.open(uploaded_file)
                alt_text = _ocr_space_fallback(image)
                if alt_text:
                    text = alt_text
                else:
                    text = (
                        "⚠️ Image OCR is not supported in this deployment environment.\n"
                        "Please upload PDF/TXT/CSV files or paste text manually."
                    )
            except Exception:
                text = (
                    "⚠️ Image OCR is not supported in this deployment environment.\n"
                    "Please upload PDF/TXT/CSV files or paste text manually."
                )

    elif file_type == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif file_type == "csv":
        df = pd.read_csv(uploaded_file)
        if "doctor_prescription" in df.columns:
            text = str(df["doctor_prescription"].iloc[0])
        else:
            text = "⚠️ CSV does not contain 'doctor_prescription' column."
        numeric_data = df.iloc[0].to_dict()

    return text, numeric_data
