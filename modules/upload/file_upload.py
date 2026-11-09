import pandas as pd
import io
from modules.upload.delimiter_utils import detect_delimiter

def load_file(uploaded_file, delimiter=None):
    if uploaded_file is None:
        return None, None

    try:
        if uploaded_file.name.endswith(".csv"):
            content = uploaded_file.read().decode("utf-8")
            uploaded_file.seek(0)

            # Use imported utility function
            detected = detect_delimiter(content)
            sep = delimiter if delimiter else detected

            df = pd.read_csv(io.StringIO(content), sep=sep)
            return df, detected

        elif uploaded_file.name.endswith(".xlsx"):
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file)
            return df, None

    except Exception as e:
        print("Fehler beim Einlesen:", e)
        return None, None
