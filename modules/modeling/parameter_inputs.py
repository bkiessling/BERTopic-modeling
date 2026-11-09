import streamlit as st

# Embeddings and language inputs
def language_and_embedding(defaults=None):
    st.subheader("Embeddings und Sprache")

    models = [
        "all-MiniLM-L6-v2",  # General-purpose, small, fast
        "all-mpnet-base-v2",  # Larger, very strong embeddings
        "paraphrase-MiniLM-L12-v2",  # Small, good quality
        "jinaai/jina-embeddings-v2-base-de",  # Specialized for German
        "thenlper/gte-small",  # Multilingual, very fast
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual, fast, good quality
    ]
    
    default_model = defaults.get("embedding_model", "all-MiniLM-L6-v2") if defaults else "all-MiniLM-L6-v2"

    model = st.selectbox(
        "Embedding-Modell",
        options=models,
        index=models.index(default_model), 
        key="embedding_model_select",
        help="Wähle ein Modell aus, das für deine Textart passt.",
        format_func=lambda x: x
    )

    language = st.selectbox(
        "Sprache",
        options=["Deutsch", "Englisch"], 
        index=0 if (defaults is None or defaults["language"] == "Deutsch") else 1
    )

    return model, language

# UMAP inputs
def umap_inputs(defaults=None):
    st.subheader("UMAP")
    n_neighbors = st.slider("Anzahl Nachbarn (n_neighbors)", 5, 100, 
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
                             value=defaults.get("max_df", 0.85) if defaults else 0.85)
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

# Define default parameter inputs
def get_default_params(n_docs, avg_text_len=100):
    # === Embedding Model Auswahl basierend auf Textlänge ===
    if avg_text_len >= 100:
        embedding_model = "jinaai/jina-embeddings-v2-base-de"
    elif avg_text_len < 30:
        embedding_model = "paraphrase-MiniLM-L12-v2"
    else:
        embedding_model = "all-mpnet-base-v2"

    defaults = {
        "embedding_model": embedding_model,
        "language": "Deutsch",
        "n_components": 5,
        "min_dist": 0.1,
        "ngram_range": (1, 1) if avg_text_len < 30 else (1, 2),
        "min_df": 0.001 if n_docs < 1000 else 0.01,
        "max_df": 0.85,
        "representations": ["KeyBERT", "MMR"],
        "top_n_words": 10
    }

    # Dynamische Cluster-Parameter
    if n_docs < 1000:
        defaults["n_neighbors"] = 5
        defaults["min_cluster_size"] = 5
    elif n_docs < 10000:
        defaults["n_neighbors"] = 15
        defaults["min_cluster_size"] = 15
    else:
        defaults["n_neighbors"] = 50
        defaults["min_cluster_size"] = 30

    return defaults
