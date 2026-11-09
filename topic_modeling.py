import streamlit as st
from modules.upload.file_upload import load_file

st.title("Themenmodellierung mit BERTopic")

uploaded_file = st.file_uploader("Lade eine CSV- oder Excel-Datei hoch", type=["csv", "xlsx"])
df = load_file(uploaded_file)
