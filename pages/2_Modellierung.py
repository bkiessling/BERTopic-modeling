import streamlit as st
import pandas as pd
import numpy as np
from modules.modeling.parameter_inputs import (
    umap_inputs,
    hdbscan_inputs,
    vectorizer_inputs,
    language_and_embedding,
    representation_inputs,
    get_default_params,
    top_n_words_input,
)
from modules.modeling.train_model import train_bertopic_model
from modules.ui.explanations import show_model_explanations
from sentence_transformers import SentenceTransformer
from torch import device as torch_device, backends


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
    "Die Voreinstellungen basieren auf deinem Upload und den gewählten Textfeldern."
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
    use_cpu = "jina" in model_name.lower() or not backends.mps.is_available()
    device_str = "cpu" if use_cpu else "mps"
    return SentenceTransformer(
        model_name,
        device=torch_device(device_str),
        trust_remote_code="jina" in model_name
    )


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

# Reset training flag if parameters changed
if "last_model_params" in st.session_state:
    if st.session_state["last_model_params"] != model_params:
        st.session_state["model_trained"] = False
st.session_state["last_model_params"] = model_params


# -------------------------------
# Train model button + progress
# -------------------------------
if st.button("Modell trainieren"):
    if "cleaned_data" not in st.session_state:
        st.error("Keine bereinigten Daten vorhanden. Zuerst Daten hochladen und bereinigen.")
        st.stop()

    cleaned_df: pd.DataFrame = st.session_state["cleaned_data"]
    doc_list = cleaned_df[st.session_state["text_column"]].tolist()
    sample_info = st.session_state.get("sample_percentage", 100)

    # Prevent duplicate training if already done
    if st.session_state.get("model_trained"):
        st.info("✅ Modell wurde bereits trainiert. Überspringe erneutes Training.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        st.write(f"Training startet mit {len(doc_list)} Dokumenten "
                 f"({sample_info}% der ursprünglichen Daten).")

        # Load model only when training is requested.
        embedding_model = load_embedding_model(embedding_model_name)

        topic_model, topic_info = train_bertopic_model(
            documents=doc_list,
            params=model_params,
            embedding_model=embedding_model,
            status=status_text,
            progress=progress_bar,
        )

        # Save docs AND their matching IDs for the Analyse page
        st.session_state.update(
            {
                "topic_model": topic_model,
                "topic_info": topic_info.copy(),
                "topic_info_original": topic_info.copy(),
                "model_params": model_params,
                "display_topics": None,
                "original_topics": None,
                "original_topic_info": None,
                "original_display_topics": None,
                "original_outlier_count": int((np.array(topic_model.topics_) == -1).sum()),
                "docs": doc_list,
                "ids": cleaned_df[st.session_state["id_column"]].tolist(),  # <-- add this line
                "model_trained": True,
            }
        )

        progress_bar.progress(100)
        status_text.text("✅ Modelltraining abgeschlossen.")
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
