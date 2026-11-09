import streamlit as st
import pandas as pd
from streamlit_extras.switch_page_button import switch_page
from modules.upload.file_upload import load_file
from modules.upload.delimiter_utils import get_delimiter_label
from modules.preprocessing.text_cleaner import clean_text_column, filter_text_column
from modules.preprocessing.text_selection import build_text_df

# -------------------------------
# Streamlit app config
# -------------------------------
st.set_page_config(
    page_title="Topic Modeling with BERTopic", 
    page_icon="assets/logo.svg",
    layout="wide")
st.title("Topic Modeling with BERTopic")
st.subheader("Daten hochladen")

# -------------------------------
# File upload section
# -------------------------------

# Streamlit file uploader (accepts CSV or Excel files)
uploaded_file = st.file_uploader(label="Lade eine CSV oder Excel-Datei hoch", type=["csv", "xlsx"])

# Initialize variables
raw_data = None
detected_delimiter = None

if uploaded_file is not None:
    # Load once initially to auto-detect the delimiter if it's a CSV
    temp_df, detected_delimiter = load_file(uploaded_file, delimiter=None)

    # If it's a CSV file and a delimiter was detected
    if uploaded_file.name.endswith(".csv") and detected_delimiter:
        # Ask user to confirm or adjust the auto-detected delimiter
        delimiter = st.radio(
            "Wähle CSV-Trennzeichen",
            options=[",", ";", "\t"],
            index={",": 0, ";": 1, "\t": 2}[detected_delimiter],
            format_func=get_delimiter_label,
            horizontal=True
        )
        # Reload file using selected delimiter
        raw_data, _ = load_file(uploaded_file, delimiter=delimiter)

    # If it's an Excel file, load directly (no delimiter needed)
    elif uploaded_file.name.endswith(".xlsx"):
        raw_data, _ = load_file(uploaded_file)

    # Show file info and preview
    if raw_data is not None:
        num_rows, num_cols = raw_data.shape
        st.success(f"Daten erfolgreich geladen: {num_rows} Zeilen, {num_cols} Spalten")
        st.markdown("#### Vorschau")
        st.dataframe(raw_data, use_container_width=True, hide_index=True, height=250)

# -------------------------------
# Data cleaning section
# -------------------------------
if raw_data is not None:
    st.markdown("---")
    st.subheader("Daten bereinigen")

    # Identify columns with text content
    text_col_candidates = raw_data.select_dtypes(include="object").columns.tolist()

    # Let user choose an ID column, or auto-generate one
    id_col_options = raw_data.columns.tolist()
    id_col_options.insert(0, "ID generieren")
    selected_id_col = st.selectbox("Wähle ID-Spalte", options=id_col_options)

    # Let user choose one or more text columns
    selected_cols = st.multiselect("Wähle eine oder mehrere Textspalten", options=text_col_candidates)

    # User-defined stopwords ---
    custom_stopwords_input = st.text_input(
        "Wörter zum Entfernen (durch Komma getrennt), meist nicht notwendig",
        placeholder="z. B. NDR, Eigennamen, usw."
    )

    # Sampling percentage slider 
    sample_percentage = st.slider(
        "Prozentsatz der Stichprobe",
        min_value=0,
        max_value=100,
        value=100,
        step=5,
        format="%d%%"
    )

    if st.button("Daten bereinigen"):
        try:
            if not selected_cols:
                st.error("Bitte wähle mindestens eine Textspalte aus.")
                st.stop()

            # Build ['id', 'text'] long DataFrame
            selected_data = build_text_df(raw_data, selected_cols, selected_id_col)

            # Apply sampling if slider < 100%
            if sample_percentage < 100:
                frac = sample_percentage / 100.0
                selected_data = selected_data.sample(frac=frac, random_state=42).reset_index(drop=True)
                st.warning(f"Nur {sample_percentage}% der Daten verwendet ({len(selected_data)} Zeilen).")

            # Clean and filter text
            cleaned_data = clean_text_column(selected_data, text_column="text")
            cleaned_data = filter_text_column(cleaned_data, text_column="text")

            # --- Apply user-provided stopword removal ---
            if custom_stopwords_input.strip():
                stopword_list = [
                    w.strip().lower() for w in custom_stopwords_input.split(",") if w.strip()
                ]

                def remove_custom_words(text):
                    for w in stopword_list:
                        text = text.replace(f" {w} ", " ")
                        if text.startswith(w + " "):
                            text = text[len(w) + 1:]
                        if text.endswith(" " + w):
                            text = text[:-len(w) - 1]
                    return " ".join(text.split())

                cleaned_data["text"] = cleaned_data["text"].apply(remove_custom_words)

            # Save all relevant data in session state
            st.session_state.update({
                "raw_text_df": selected_data,
                "cleaned_data": cleaned_data,
                "text_column": "text",
                "id_column": "id",
                "num_text_columns": len(selected_cols),
                "original_text_columns": selected_cols,
                "avg_text_len": cleaned_data["text"].str.len().mean(),
                "custom_stopwords": custom_stopwords_input,
                "sample_percentage": sample_percentage,
            })

            st.success(
                f"Daten erfolgreich bereinigt. "
                f"{'Nur ' + str(sample_percentage) + '% verwendet. ' if sample_percentage < 100 else ''}"
                "NAs, Zahlen, Sonderzeichen und URLs entfernt; Text in Kleinbuchstaben konvertiert."
                + (" Benutzerdefinierte Wörter entfernt." if custom_stopwords_input.strip() else "")
            )

        except Exception as e:
            st.error(f"Fehler bei der Bereinigung: {e}")

# -------------------------------
# Preview cleaned results
# -------------------------------
if "cleaned_data" in st.session_state and "raw_text_df" in st.session_state:
    text_df = st.session_state["raw_text_df"]
    cleaned_data = st.session_state["cleaned_data"]
    avg_len = st.session_state.get("avg_text_len", 0)

    initial_count = len(text_df)
    cleaned_count = len(cleaned_data)

    st.markdown("#### Vorschau bereinigter Daten")

    # Show key metrics
    col_raw, col_cleaned, col_avg_length = st.columns(3)
    col_raw.metric("Zeilen vor Bereinigung", f"{initial_count:,.0f}".replace(",", "."))
    col_cleaned.metric("Zeilen nach Bereinigung", f"{cleaned_count:,.0f}".replace(",", "."))
    col_avg_length.metric("⌀ Textlänge", f"{round(avg_len)}")

    # Show cleaned data
    st.dataframe(cleaned_data, use_container_width=True, hide_index=True, height=250)

    st.markdown("---")
    if st.button("Weiter zur Modellierung"):
        st.switch_page("pages/2_Modellierung.py")
