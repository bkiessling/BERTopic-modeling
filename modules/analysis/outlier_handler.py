# Module to reduce outliers after topic modeling
import numpy as np
import pandas as pd

def reduce_outliers(
    topic_model,
    docs,
    embeddings,
    threshold: float,
    top_n_words: int,
    session_state,
):
    """
    • Saves originals to session_state (only first call)
    • Calls BERTopic.reduce_outliers + update_topics
    • Rebuilds topic_info and display_topics
    • Returns True on success
    """
    # --- Save originals (only once) ---------------------------------
    if (
        "original_topic_info" not in session_state
        or session_state.get("original_topic_info") is None
    ):
        session_state["original_topic_info"] = session_state["topic_info"].copy()
        session_state["original_display_topics"] = session_state["display_topics"].copy()

    # --- BERTopic outlier reduction ---------------------------------
    new_topics = topic_model.reduce_outliers(
        documents=docs,
        topics=topic_model.topics_,
        embeddings=np.array(embeddings),
        threshold=threshold,
    )

    topic_model.update_topics(
        docs=docs,
        topics=new_topics,
        vectorizer_model=topic_model.vectorizer_model,
        representation_model=topic_model.representation_model,
    )

    # --- Rebuild topic_info & display_topics ------------------------
    topic_info = topic_model.get_topic_info()

    fmt = lambda x: ", ".join(x[:top_n_words]) if isinstance(x, list) else x
    for col in ["Representation", "KeyBERT", "MMR"]:
        if col in topic_info.columns:
            topic_info[col] = topic_info[col].apply(fmt)

    topic_info["Percentage"] = (topic_info["Count"] / len(docs) * 100).round(2)

    display_topics = topic_info.rename(
        columns={
            "Topic": "Thema",
            "Name": "Bezeichnung",
            "Count": "Dokumente (n)",
            "Percentage": "Anteil (%)",
            "Representation": "Keywords",
        }
    )

    for col in ["KeyBERT", "MMR"]:
        if col not in display_topics.columns:
            display_topics[col] = ""
    display_topics = display_topics[
        ["Thema", "Dokumente (n)", "Anteil (%)", "Keywords", "KeyBERT", "MMR"]
    ]

    # --- Persist back to session_state ------------------------------
    session_state["topic_info"] = topic_info
    session_state["display_topics"] = display_topics
    return True
