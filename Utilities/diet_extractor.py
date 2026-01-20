import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd

def extract_text(uploaded_file):
    text = ""
    numeric_data = None
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    elif file_type in ["png", "jpg", "jpeg"]:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)

    elif file_type == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif file_type == "csv":
        df = pd.read_csv(uploaded_file)
        text = df["doctor_prescription"].iloc[0]
        numeric_data = df.iloc[0].to_dict()

    return text, numeric_data

