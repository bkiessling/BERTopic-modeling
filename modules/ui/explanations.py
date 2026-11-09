import streamlit as st

def show_model_explanations(
    embedding_model_name,
    language,
    n_neighbors,
    n_components,
    min_dist,
    min_cluster_size,
    ngram_range,
    min_df,
    max_df,
    selected_representations,
    top_n_words
):
    st.markdown("#### Embeddings und Sprache")
    with st.container():
        st.markdown(f"""
        Embeddings sind numerische Vektoren, die den Bedeutungsgehalt von Texten abbilden.
        BERTopic nutzt sie, um ähnliche Inhalte zu gruppieren und Themen zu erkennen.
        Es gibt tausende Embedding-Modelle, z. B. für bestimmte Sprachen oder welche, die besonders schnell sind.
        Eine Auswahl findest du hier: [HuggingFace MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard).

        - **Embedding-Modell**: `{embedding_model_name}`
        - **Sprache**: `{language}`
        """)

    st.markdown("#### UMAP")
    with st.container():
        st.markdown(f"""
        UMAP (Uniform Manifold Approximation and Projection) reduziert die komplexen Embeddings auf wenige Dimensionen,
        damit sie effizienter verarbeitet und visualisiert werden können.

        - **n_neighbors**: `{n_neighbors}` – bestimmt, wie viele Nachbarn pro Punkt berücksichtigt werden.
          Kleine Werte → lokale Cluster; große Werte → globale Strukturen.

        - **n_components**: `{n_components}` – Anzahl der Ziel-Dimensionen (typisch: 2–5).

        - **min_dist**: `{min_dist}` – definiert, wie eng Punkte gruppiert werden dürfen.
          Kleine Werte führen zu dichteren Clustern.
        """)

    st.markdown("#### HDBSCAN")
    with st.container():
        st.markdown(f"""
        HDBSCAN ist ein Clustering-Algorithmus, der die Anzahl der Cluster automatisch bestimmt.
        Er basiert auf Dichte und ist robust gegenüber Ausreißern.

        - **min_cluster_size**: `{min_cluster_size}` – minimale Anzahl an Dokumenten pro Cluster.
          Kleine Werte → mehr, kleinere Cluster; große Werte → weniger, stabilere Cluster.
        """)

    st.markdown("#### Vektorisierung")
    with st.container():
        st.markdown(f"""
        Nach dem Clustering wandelt der Vektorisierer zusammengefasste Themen-Texte in zählbare Einheiten wie Wörter oder Phrasen um.
        BERTopic nutzt diese Informationen, um jedes Thema mit repräsentativen Begriffen zu versehen.

        - **ngram_range**: `{ngram_range}` – legt fest, ob Einzelwörter oder auch Wortfolgen betrachtet werden.

        - **min_df**: `{min_df}` – ein Begriff muss mindestens in so vielen Themen-Texten vorkommen, um berücksichtigt zu werden.

        - **max_df**: `{max_df}` – Begriffe, die in zu vielen Themen-Texten vorkommen, werden ignoriert (z. B. "und", "ist").
        """)

    st.markdown("#### Repräsentationsmodelle")
    with st.container():
        keybert_status = "ausgewählt" if "KeyBERT" in selected_representations else ""
        mmr_status = "ausgewählt" if "MMR" in selected_representations else ""

        st.markdown(f"""
        BERTopic nutzt Repräsentationsmodelle, um Cluster mit beschreibenden Begriffen zu versehen:

        - **KeyBERT**: `{keybert_status}` – nutzt Embedding-Ähnlichkeit, um relevante Begriffe auszuwählen.
        - **MMR**: `{mmr_status}` – reduziert Redundanz, indem es Relevanz und Diversität balanciert.
        - **Top n Words** `{top_n_words}` - Anzahl der Keywords, die pro Thema angezeigt werden
        """)

        if not selected_representations:
            st.markdown("*Kein Repräsentationsmodell ausgewählt – Die c-TF-IDF-Begriffe werden ohne zusätzliche Repräsentationsmodelle verwendet.*")
