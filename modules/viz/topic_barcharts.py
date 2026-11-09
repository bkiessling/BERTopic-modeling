import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


def _plot_barcharts(
    topic_model,
    topics: list[int],
    topic_labels: list[str],
    top_n_words: int,
    width: int,
    height: int,
):
    """Hilfsfunktion: Plotte Bar-Charts für die angegebenen Topics mit Labels als Titel."""

    n_rows = len(topics)
    fig = make_subplots(
        rows=n_rows,
        cols=1,
        subplot_titles=topic_labels,
        vertical_spacing=0.1,
    )

    # -- Alle Scores sammeln, um max Wert zu bestimmen (für unified X-Achse)
    all_scores = []
    topic_word_data = []

    for topic in topics:
        words = (topic_model.get_topic(topic) or [])[:top_n_words]
        terms = [w for w, _ in words][::-1]
        scores = [s for _, s in words][::-1]
        all_scores.extend(scores)
        topic_word_data.append((terms, scores))

    x_max = max(all_scores, default=1.0) or 1.0

    # -- Plot each chart
    for idx, (terms, scores) in enumerate(topic_word_data):
        row = idx + 1
        fig.add_trace(
            go.Bar(
                x=scores,
                y=terms,
                orientation="h",
                showlegend=False,
                marker=dict(color="#1f77b4"),
                hovertemplate="<b>%{y}</b><br>Relevanz: %{x:.2f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        fig.update_xaxes(
            title_text="Repräsentationsgewicht",
            range=[0, x_max * 1.05],
            row=row,
            col=1,
            showgrid=False,
        )
        fig.update_yaxes(showgrid=False)

    fig.update_layout(
        height=height,
        width=width,
        title_text="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig
