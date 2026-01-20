import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd

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
            text = pytesseract.image_to_string(image)
            if not text.strip():
                text = (
                    "⚠️ OCR produced empty text.\n"
                    "Please upload PDF/TXT/CSV or paste text manually."
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
