"""Credential lookup and optional naming controls, confined to the UI boundary."""
import os
import streamlit as st
from modules.analysis.topic_naming import DEFAULT_NAMING_MODEL, name_topics, topic_keywords


def openai_key():
    for name in ('BERTOPIC_OPENAI_API_KEY', 'OPENAI_API_KEY'):
        value = os.environ.get(name, '').strip()
        if value:
            return value
    try:
        return str(st.secrets.get('BERTOPIC_OPENAI_API_KEY') or st.secrets.get('OPENAI_API_KEY') or '').strip()
    except (FileNotFoundError, KeyError):
        return ''


def naming_options():
    st.subheader('OpenAI-Verbindung')
    key_present = bool(openai_key())
    st.caption('API-Key: erkannt; Zugriff noch nicht geprüft.' if key_present else 'API-Key: nicht hinterlegt.')
    enabled = st.checkbox('Themen mit OpenAI benennen (nur Keywords)',
                          value=False, disabled=not key_present, key='use_openai_naming')
    with st.expander('Einrichtung und Datenübertragung'):
        st.caption('Übertragen werden pro Thema bis zu zehn Keywords und die Themen-ID; keine Originaltexte, Dokumentauszüge, Dokument-IDs oder Embeddings. Keywords können vertrauliche Begriffe enthalten. API-Nutzung kostet zusätzlich; ChatGPT Pro deckt sie nicht ab.')
        if not key_present:
            st.caption('OPENAI_API_KEY als Umgebungsvariable oder in .streamlit/secrets.toml hinterlegen und die App neu starten.')
        else:
            st.caption('Gültigkeit, Modellzugriff und Guthaben werden erst beim Benennen geprüft.')
        model = st.text_input('OpenAI-Modell für Themennamen', value=DEFAULT_NAMING_MODEL,
                              disabled=not enabled or not key_present, key='openai_naming_model')
    return enabled and key_present, model.strip()


def generate_names(analysis, api_key, model):
    labels = name_topics(topic_keywords(analysis.result.model), analysis.result.config.language, api_key, model)
    analysis.set_topic_names(labels, model)
