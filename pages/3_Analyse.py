import streamlit as st
import pandas as pd
import numpy as np

# Modules
from modules.analysis.outlier_handler import reduce_outliers, restore_outliers
from modules.analysis.topic_table import build_topic_table, compute_topic_stats
from modules.analysis.document_table import build_document_table

from modules.viz.topic_network import plot_topic_network
from modules.viz.topic_barcharts import plot_topic_barcharts
from modules.viz.topic_similarity import plot_topic_similarity

# -------------------------------
# Streamlit app config
# -------------------------------
st.set_page_config(page_title="Analyse", 
                   page_icon="assets/logo.svg",
                   layout="wide")
st.markdown("# Topic-Modeling mit BERTopic")
st.subheader("Analyse der Ergebnisse")

# -------------------------------
# Guard – ensure model exists
# -------------------------------
if "topic_model" not in st.session_state or "topic_info" not in st.session_state:
    st.error("Kein Modell gefunden. Bitte zuerst ein Modell trainieren.")
    st.stop()

# -------------------------------
# Load essentials from session
# -------------------------------
topic_model   = st.session_state["topic_model"]
topic_info    = st.session_state["topic_info"]
cleaned_data  = st.session_state["cleaned_data"]
docs          = st.session_state["docs"]
ids = st.session_state.get(
    "ids",
    cleaned_data[st.session_state["id_column"]].tolist()
)
top_n_words   = st.session_state.get("model_params", {}).get("top_n_words", 10)

# -------------------------------
# Prepare topic overview table
# -------------------------------
if "display_topics" not in st.session_state or st.session_state["display_topics"] is None:
    st.session_state["display_topics"] = build_topic_table(
        topic_info=topic_info,
        docs=docs,
        top_n_words=top_n_words
    )

# -------------------------------
# Sidebar – Outlier controls
# -------------------------------
st.sidebar.header("Outlier reduzieren")
threshold = st.sidebar.slider(
    "Schwellwert (Threshold)",
    0.0, 0.5, 0.05, 0.01,
    help="Thema -1 sind Ausreißer. Ein kleinerer Threshold ordnet mehr Dokumente bestehenden Topics zu."
)

# Reduce outliers
if st.sidebar.button("Outlier reduzieren"):
    if reduce_outliers(
        topic_model=topic_model,
        docs=docs,
        embeddings=st.session_state["embeddings"],
        threshold=threshold,
        top_n_words=top_n_words,
        session_state=st.session_state,
    ):
        st.success("Outlier erfolgreich reduziert")
    else:
        st.info("Keine Ausreißer vorhanden.")

# Reset to originals
if st.sidebar.button("Outlier zurücksetzen"):
    if restore_outliers(topic_model, docs, top_n_words, st.session_state):
        st.success("Outlier wurden zurückgesetzt.")
    else:
        st.info("Keine ursprünglichen Zuordnungen gespeichert. Bitte zuerst Ausreißer reduzieren.")

# -------------------------------
# Tabs: Topics, Documents, Model parameters
# -------------------------------
st.markdown("#### Themenanalyse")
tab_overview, tab_documents, tab_params = st.tabs(
    ["Themenübersicht", "Textbeiträge", "Modell-Parameter"]
)

# --- Themenübersicht ---
with tab_overview:
    st.markdown("#### Themenübersicht")
    display_topics = st.session_state["display_topics"]
    topic_info     = st.session_state["topic_info"]

    n_topics, outl_pct, avg_docs = compute_topic_stats(topic_info, docs)

    # Metric shows topics, outlier and document length
    col_identified_topics, col_outlier, col_avg_docs = st.columns(3)
    col_identified_topics.metric("Identifizierte Themen", n_topics)
    col_outlier.metric("Outlier (Thema -1)", f"{outl_pct}%")
    col_avg_docs.metric("⌀ Dokumente / Thema", avg_docs)

    st.dataframe(display_topics, width="stretch", hide_index=True)

# --- Textbeiträge ---
with tab_documents:
    st.markdown("#### Textbeiträge")
    
    main_txt_col = st.session_state.get("original_text_columns", ["Textbeitrag"])[0]
    doc_topics = topic_model.topics_

    view_mode = "Textbeitrag"
    total_texts = len(docs)
    unique_ids = len(set(ids))

    if unique_ids < total_texts:
        view_mode = st.radio(
            "Sortierung wählen",
            ["Textbeitrag", "ID"],
            help="Textbeitrag: jede Zeile einzeln\nID: Beiträge pro ID gruppiert",
            horizontal=True,
        )

    # Build document table with appropriate format
    display_documents = build_document_table(
        ids=ids,
        docs=docs,
        doc_topics=doc_topics,
        topic_info=topic_info,
        main_txt_col=main_txt_col,
        view_mode=view_mode,
    )

    # Compute and show stats
    total, uniq = total_texts, unique_ids
    col_ids, col_texts, _ = st.columns(3)
    col_ids.metric("Unique IDs", f"{uniq:,.0f}".replace(",", "."))
    col_texts.metric("Textbeiträge (n)", f"{total:,.0f}".replace(",", "."))
    
    st.dataframe(display_documents, width="stretch", hide_index=True)

# --- Modell-Parameter ---
with tab_params:
    st.markdown("#### Modell-Parameter")
    params = st.session_state.get("model_params", {})
    rows = [
        {"Parameter": k if not isinstance(v, dict) else f"{k}.{sub_k}", "Wert": str(sub_v)}
        for k, v in params.items()
        for sub_k, sub_v in (v.items() if isinstance(v, dict) else {None: v}.items())
    ]
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("Keine Modellparameter gefunden.")

# -------------------------------
# Visualisation Tabs
# -------------------------------
st.markdown("#### Visualisierung")
tab_sim, tab_bars, tab_net = st.tabs(["Themen-Ähnlichkeit", "Top-Keywords", "Dokumentenkarte"])

# Topic similarity matrix
with tab_sim:
    st.markdown("##### Themen-Ähnlichkeit")
    st.caption("Die Matrix zeigt die paarweise Ähnlichkeit der identifizierten Themen auf Basis ihrer Repräsentationen. "
               "Es werden maximal 20 Themen dargestellt. " 
               "Eine hohe Kosinus-Ähnlichkeit weist auf eine starke thematische Überschneidung hin.")
    with st.spinner("Berechne Ähnlichkeiten …"):
        st.plotly_chart(
            plot_topic_similarity(topic_model, top_n_topics=20),
            width="stretch",
        )
        
# Top word for top six topics
with tab_bars:
    st.markdown("##### Top-Keywords")
    st.caption(
    "Die Balkendiagramme zeigen die wichtigsten Keywords für die häufigsten Themen. "
    "Die angezeigten Gewichte stammen aus der gewählten Themenrepräsentation; sie sind keine Wahrscheinlichkeiten. "
    )
    with st.spinner("Erstelle Balkendiagramme …"):
        plot_topic_barcharts(topic_model=topic_model)


# Topic network
with tab_net:
    st.markdown("##### Dokumentenkarte")
    st.caption(
    "Die Dokumentenkarte zeigt die Verteilung und Nähe der Themen im zweidimensionalen Raum. "
    "Thematisch ähnliche Topics liegen näher beieinander. "
    "Jeder Punkt repräsentiert einen Textbeitrag, die Farben clustern die Punkte nach Thema. "
    )
    with st.spinner("Berechne Layout …"):
        st.plotly_chart(
            plot_topic_network(
                topic_model=topic_model,
                topics=topic_model.topics_,  # <- pass topics explicitly
                docs=docs,
                embeddings=np.array(st.session_state["embeddings"]),
                dim_reduction="umap",
                top_n_legend=20,
                width=1000,
                height=700,
            ),
            width="stretch",
        )

