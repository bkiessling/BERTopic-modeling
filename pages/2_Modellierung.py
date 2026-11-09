import streamlit as st
import logging
from modules.ui.modeling_inputs import (
    umap_inputs,
    hdbscan_inputs,
    vectorizer_inputs,
    language_and_embedding,
    representation_inputs,
    top_n_words_input,
)
from modules.modeling.train_model import train_bertopic_model
from modules.ui.explanations import show_model_explanations
from sentence_transformers import SentenceTransformer
import torch
from modules.modeling.configuration import TrainingConfig, get_default_params
from modules.ui.analysis_state import AnalysisState


# -------------------------------
# Streamlit app config
# -------------------------------
st.set_page_config(page_title="Modell konfigurieren",
                   page_icon="assets/logo.svg",
                   layout="wide")
st.markdown("# Topic-Modeling mit BERTopic")
st.subheader("Modell konfigurieren")
st.markdown(
    "Definiere die Modellparameter in der Sidebar. "
    "Die Clusterparameter berücksichtigen die Textanzahl. Wähle Sprache und Embedding-Modell bewusst aus."
)


# -------------------------------
# Sidebar – parameter inputs
# -------------------------------
st.sidebar.header("Modellparameter")

default_params = get_default_params(
    n_docs=len(st.session_state.get("cleaned_data", [])),
    avg_text_len=st.session_state.get("avg_text_len", 50),
)

with st.sidebar:
    # Embedding & language
    embedding_model_name, language = language_and_embedding(default_params)
    # UMAP hyper-parameters
    n_neighbors, n_components, min_dist = umap_inputs(default_params)
    # HDBSCAN hyper-parameters
    min_cluster_size = hdbscan_inputs(default_params)
    # Vectorizer settings
    ngram_range, min_df, max_df = vectorizer_inputs(default_params)
    # Topic representation methods
    selected_reprs = representation_inputs(default_params)
    # Top-N words shown per topic
    top_n_words = top_n_words_input(default_params)


# -------------------------------
# Load embedding model (cached)
# -------------------------------
@st.cache_resource
def load_embedding_model(model_name):
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    return SentenceTransformer(model_name, device=device, trust_remote_code=False,
                               model_kwargs={"use_safetensors": True})


if "cleaned_data" not in st.session_state or st.session_state["cleaned_data"].empty:
    st.info("Bitte zuerst Daten hochladen und bereinigen.")
    st.stop()


# -------------------------------
# Collect parameters in one dict
# -------------------------------
model_params = {
    "embedding_model": embedding_model_name,
    "language": language,
    "umap": {
        "n_neighbors": n_neighbors,
        "n_components": n_components,
        "min_dist": min_dist,
    },
    "hdbscan": {"min_cluster_size": min_cluster_size},
    "vectorizer": {
        "ngram_range": ngram_range,
        "min_df": min_df,
        "max_df": max_df,
    },
    "representation_models": selected_reprs,
    "top_n_words": top_n_words,
}

config = TrainingConfig.from_dict(model_params)
cleaned_df = st.session_state["cleaned_data"]
doc_list = cleaned_df[st.session_state["text_column"]].tolist()
validation_errors = config.validate(doc_list)
for message in validation_errors:
    st.error(message)

if st.button("Modell trainieren", disabled=bool(validation_errors)):
    progress_bar = st.progress(0)
    status_text = st.empty()

    def report(percent, message):
        progress_bar.progress(percent)
        status_text.text(message)

    try:
        status_text.text("Lade Embedding-Modell …")
        embedding_model = load_embedding_model(embedding_model_name)
        result = train_bertopic_model(doc_list, config, embedding_model, on_progress=report)
        analysis = AnalysisState(
            result=result,
            ids=cleaned_df[st.session_state["id_column"]].tolist(),
            text_columns=st.session_state.get("original_text_columns", ["Textbeitrag"]),
            preprocessing={
                "sample_percentage": st.session_state.get("sample_percentage", 100),
                "custom_stopwords": st.session_state.get("custom_stopwords", ""),
                "cleaning": "lowercase; remove URLs, mentions, digits, punctuation; collapse whitespace",
            },
        )
    except ValueError as exc:
        progress_bar.empty()
        st.error(str(exc))
    except Exception:
        logging.getLogger(__name__).exception("Modelltraining fehlgeschlagen")
        progress_bar.empty()
        st.error("Das Modell konnte nicht geladen oder trainiert werden. Bitte Netzwerkzugriff, installierte Abhängigkeiten und Serverprotokoll prüfen.")
    else:
        st.session_state["analysis"] = analysis
        st.session_state.pop("topic_barchart_selection", None)
        st.switch_page("pages/3_Analyse.py")


# -------------------------------
# Show short explanations
# -------------------------------
show_model_explanations(
    embedding_model_name,
    language,
    n_neighbors,
    n_components,
    min_dist,
    min_cluster_size,
    ngram_range,
    min_df,
    max_df,
    selected_reprs,
    top_n_words,
)
