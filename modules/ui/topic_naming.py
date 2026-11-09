"""Credential lookup and optional naming controls, confined to the UI boundary."""
import os
import streamlit as st
from modules.analysis.topic_naming import DEFAULT_NAMING_MODEL, NAMING_MODELS, name_topics, topic_keywords, check_model_access, TopicNamingError


def _key_binding():
    # Project/Streamlit secrets take precedence over stale shell variables.
    try:
        for name in ('BERTOPIC_OPENAI_API_KEY', 'OPENAI_API_KEY'):
            value = str(st.secrets.get(name) or '').strip()
            if value:
                return value, f'Streamlit-Secrets · {name}'
    except (FileNotFoundError, KeyError):
        pass
    for name in ('BERTOPIC_OPENAI_API_KEY', 'OPENAI_API_KEY'):
        value = os.environ.get(name, '').strip()
        if value:
            return value, f'Umgebungsvariable · {name}'
    return '', ''


def openai_key():
    return _key_binding()[0]


def naming_model_select(key, disabled=False, default=DEFAULT_NAMING_MODEL):
    names = list(NAMING_MODELS)
    if default not in names:
        default = DEFAULT_NAMING_MODEL
    return st.selectbox('OpenAI-Modell für Themennamen', names, index=names.index(default),
                        format_func=lambda name: NAMING_MODELS[name], disabled=disabled, key=key)


def access_check_button(api_key, model):
    if st.button('API-Zugriff prüfen', disabled=not bool(api_key), key='check_openai_access'):
        try:
            check_model_access(api_key, model)
        except TopicNamingError as exc:
            st.error(str(exc))
        else:
            st.success('API-Key akzeptiert und Modell sichtbar. Responses-Berechtigung und Guthaben werden beim Benennen geprüft.')
    st.caption('Die Prüfung sendet keine Texte und erzeugt keine Antworten. Bei eingeschränkten Keys kann die Modellabfrage gesperrt sein, obwohl Benennung erlaubt ist.')


def naming_options():
    st.subheader('OpenAI-Verbindung')
    api_key = openai_key()
    key_present = bool(api_key)
    st.caption('API-Key: erkannt; Zugriff noch nicht geprüft.' if key_present else 'API-Key: nicht hinterlegt.')
    if key_present:
        source = _key_binding()[1]
        if source:
            st.caption(f'Quelle: {source}')
    enabled = st.checkbox('Themen mit OpenAI benennen (nur Keywords)',
                          value=False, disabled=not key_present, key='use_openai_naming')
    model = naming_model_select('openai_naming_model', disabled=not key_present)
    access_check_button(api_key, model)
    with st.expander('Einrichtung und Datenübertragung'):
        st.caption('Übertragen werden pro Thema bis zu zehn Keywords und die Themen-ID; keine Originaltexte, Dokumentauszüge, Dokument-IDs oder Embeddings. Keywords können vertrauliche Begriffe enthalten. API-Nutzung kostet zusätzlich; ChatGPT Pro deckt sie nicht ab.')
        if not key_present:
            st.caption('OPENAI_API_KEY als Umgebungsvariable oder in .streamlit/secrets.toml hinterlegen und die App neu starten.')
        else:
            st.caption('Gültigkeit, Modellzugriff und Guthaben werden erst beim Benennen geprüft.')
    return enabled and key_present, model.strip()


def generate_names(analysis, api_key, model):
    labels = name_topics(topic_keywords(analysis.result.model), analysis.result.config.language, api_key, model)
    analysis.set_topic_names(labels, model)
