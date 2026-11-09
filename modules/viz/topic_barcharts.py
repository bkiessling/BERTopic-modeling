from modules.viz.bar_chart import _plot_barcharts
import streamlit as st


def plot_topic_barcharts(
    topic_model,
    top_n_words: int = 5,
    n_cols: int = 1,
    max_select: int = 4,
    width: int = 1000,
    height_per_chart: int = 400,
    topic_names=None,
):
    """
    Interaktive Version des Topic-Barplots mit auswählbaren Themen.

    - Ein Chart pro Zeile
    - Maximal 4 Themen gleichzeitig
    - Einheitliche X-Achse für Vergleichbarkeit
    """

    # -- Lade und bereite Topic-Infos vor
    info_df = topic_model.get_topic_info()
    all_topics = info_df[info_df.Topic != -1].copy()
    topic_names = topic_names or {}
    all_topics["Label"] = [f"{int(row.Topic)}_{topic_names[int(row.Topic)]}" if int(row.Topic) in topic_names else row.Name
                           for row in all_topics.itertuples()]

    # -- Voreinstellung: Top-N Topics nach Häufigkeit
    top_labels = (
        all_topics.nlargest(max_select, "Count")["Label"].tolist()
    )

    label_to_id = dict(zip(all_topics["Label"], all_topics["Topic"]))

    # -- Auswahl-Widget
    selected_labels = st.multiselect(
        "Themen auswählen:",
        options=all_topics["Label"].tolist(),
        default=top_labels,
        max_selections=max_select,
        key="topic_barchart_selection",
        help=f"Wähle bis zu {max_select} Themen aus.",
    )

    if not selected_labels:
        st.info("Keine Themen ausgewählt.")
        return

    if len(selected_labels) > max_select:
        st.warning(f"Bitte wähle maximal {max_select} Themen aus.")
        return

    selected_topics = [label_to_id[label] for label in selected_labels]

    # -- Plot
    fig = _plot_barcharts(
        topic_model=topic_model,
        topics=selected_topics,
        topic_labels=selected_labels,
        top_n_words=top_n_words,
        width=width,
        height=height_per_chart * len(selected_topics),  # dynamic height
    )
    st.plotly_chart(fig, width="stretch")
