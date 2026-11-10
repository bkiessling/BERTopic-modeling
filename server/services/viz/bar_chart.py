"""Pure Plotly keyword charts for topic keyword comparisons."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


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
