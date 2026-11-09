import streamlit as st

from modules.modeling.configuration import MODELS, MODEL_OPTIONS, recommended_model


def language_and_embedding(defaults=None):
    st.subheader("Embeddings und Sprache")
    language = st.selectbox("Sprache", ["Deutsch", "Englisch"], key="model_language")
    models = [name for name, languages in MODELS.items() if language in languages]
    default = recommended_model(language)
    model = st.selectbox(
        "Embedding-Modell", models, index=models.index(default),
        key=f"embedding_model_{language}",
        format_func=lambda name: MODEL_OPTIONS[name].label,
        help="Für Deutsch werden mehrsprachige Modelle angeboten. Die Textlänge bestimmt nicht die Sprachunterstützung.",
    )
    st.caption(f"{len(models)} Modelle verfügbar. Pro Trainingslauf wird ein Modell verwendet.")
    st.caption(MODEL_OPTIONS[model].description)
    st.markdown(f"[Modellkarte auf Hugging Face](https://huggingface.co/{model})")
    return model, language

# UMAP inputs
def umap_inputs(defaults=None):
    st.subheader("UMAP")
    n_neighbors = st.slider("Anzahl Nachbarn (n_neighbors)", 2, 100,
                            value=defaults.get("n_neighbors", 15) if defaults else 15)
    n_components = st.slider("Anzahl Dimensionen (n_components)", 2, 50,
                             value=defaults.get("n_components", 5) if defaults else 5)
    min_dist = st.slider("Minimale Distanz (min_dist)", 0.0, 1.0,
                         value=defaults.get("min_dist", 0.1) if defaults else 0.1)
    return n_neighbors, n_components, min_dist

# HDBSCAN inputs
def hdbscan_inputs(defaults=None):
    st.subheader("HDBSCAN")
    min_cluster_size = st.slider("Minimale Clustergröße", 2, 100,
                                 value=defaults.get("min_cluster_size", 10) if defaults else 10)
    return min_cluster_size

# Vector inputs
def vectorizer_inputs(defaults=None):
    st.subheader("Vektorisierung")
    ngram_range = st.selectbox("N-Gramm Bereich", options=[(1,1), (1,2), (1,3)],
                               index=[(1,1), (1,2), (1,3)].index(defaults.get("ngram_range", (1,2))) if defaults else 1)
    min_df = st.number_input("Minimale Dokumenthäufigkeit (min_df)", 0.0001, 1.0,
                             value=defaults.get("min_df", 0.001) if defaults else 0.001)
    max_df = st.number_input("Maximale Dokumenthäufigkeit (max_df)", 0.1, 1.0,
                             value=defaults.get("max_df", 0.85) if defaults else 1.0)
    return ngram_range, min_df, max_df

# Representation inputs
def representation_inputs(defaults=None):
    st.subheader("Repräsentationsmodelle")
    default_models = defaults.get("representations", ["KeyBERT", "MMR"]) if defaults else ["KeyBERT", "MMR"]
    selected_models = st.multiselect(
        "Modelle zur Themenbeschreibung",
        options=["KeyBERT", "MMR"],
        default=default_models
    )
    return selected_models

# Top n words inputs
def top_n_words_input(defaults=None):
    return st.slider(
        "Top n Words",
        min_value=5,
        max_value=30,
        value=defaults.get("top_n_words", 10) if defaults else 10,
        help="Anzahl der wichtigsten Begriffe zur Beschreibung eines Themas."
    )
