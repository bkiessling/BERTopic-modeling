# modules/modeling/train_model.py
import numpy as np
import pandas as pd
import streamlit as st
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
import umap
import hdbscan
import nltk
from nltk.corpus import stopwords
from typing import List, Tuple, Dict, Any


# Ensure stopwords are downloaded once (move this to app start later if needed)
nltk.download("stopwords")


def train_bertopic_model(
    documents: List[str],
    params: Dict[str, Any],
    embedding_model: SentenceTransformer,
    status: st.delta_generator.DeltaGenerator,
    progress: st.delta_generator.DeltaGenerator,
) -> Tuple[BERTopic, pd.DataFrame]:
    """
    Train a BERTopic model with custom parameters.
    """

    # -------------------------------
    # Step 1: Generate sentence embeddings
    # -------------------------------

    status.text("1/6: Berechne Embeddings …")

    batch_size = 4 if "jina" in params["embedding_model"].lower() else 32

    embeddings = embedding_model.encode(
        documents,
        batch_size=batch_size,
        show_progress_bar=True
    )

    progress.progress(20)

    # -------------------------------
    # Step 2: Dimensionality reduction with UMAP
    # -------------------------------

    status.text("2/6: Reduziere Dimensionen (UMAP) …")

    umap_model = umap.UMAP(
        n_neighbors=params["umap"]["n_neighbors"],
        n_components=params["umap"]["n_components"],
        min_dist=params["umap"]["min_dist"],
        metric="cosine"
    )
    progress.progress(30)

    # -------------------------------
    # Step 3: Clustering with HDBSCAN
    # -------------------------------

    status.text("3/6: Clustere mit HDBSCAN …")

    hdbscan_model = hdbscan.HDBSCAN(
        min_cluster_size=params["hdbscan"]["min_cluster_size"],
        metric="euclidean",
        prediction_data=True
    )
    progress.progress(40)

    # -------------------------------
    # Step 4: Text vectorization using CountVectorizer
    # -------------------------------

    status.text("4/6: Baue Vektorisierung …")

    language = params["language"].lower()

    stop_words = stopwords.words("german") if language == "deutsch" else "english"

    vectorizer_model = CountVectorizer(
        ngram_range=params["vectorizer"]["ngram_range"],
        min_df=params["vectorizer"]["min_df"],
        max_df=params["vectorizer"]["max_df"],
        stop_words=stop_words
    )

    ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True)
    progress.progress(50)

    # -------------------------------
    # Step 5: Configure representation models
    # -------------------------------

    status.text("5/6: Extrahiere Repräsentationen …")

    top_n_words = params.get("top_n_words", 10)
    representation_models = {}

    if "KeyBERT" in params["representation_models"]:
        representation_models["KeyBERT"] = KeyBERTInspired(top_n_words=top_n_words)
    if "MMR" in params["representation_models"]:
        representation_models["MMR"] = MaximalMarginalRelevance(top_n_words=top_n_words)

    progress.progress(60)

    # -------------------------------
    # Step 6: Train BERTopic model
    # -------------------------------

    status.text("6/6: Trainiere Modell …")

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        ctfidf_model=ctfidf_model,
        representation_model=representation_models,
        calculate_probabilities=True,
        verbose=False
    )

    topics, _ = topic_model.fit_transform(documents, np.array(embeddings))
    progress.progress(90)

    topic_info = topic_model.get_topic_info()

    st.session_state.update({
        "embedding_model": embedding_model,
        "docs": documents,
        "embeddings": embeddings,
        "vectorizer_model": vectorizer_model,
        "representation_model": representation_models
    })

    return topic_model, topic_info
