"""Topic similarity with explicit BERTopic embedding alignment."""

import numpy as np
import plotly.graph_objects as go
from sklearn.metrics.pairwise import cosine_similarity


def plot_topic_similarity(topic_model, top_n_topics: int = 20, topic_names=None):
    topic_names = topic_names or {}
    info = topic_model.get_topic_info()
    selected = info[info.Topic != -1].nlargest(top_n_topics, "Count")
    if selected.empty:
        fig = go.Figure()
        fig.add_annotation(text="Keine Themen außer Ausreißern vorhanden.", showarrow=False)
        return fig

    # BERTopic stores embeddings in ascending topic-ID order, including -1.
    # DataFrame row indices/order need not match that order.
    embedding_rows = {topic: row for row, topic in enumerate(sorted(info.Topic))}
    embeddings = np.asarray(topic_model.topic_embeddings_)
    indices = [embedding_rows[topic] for topic in selected.Topic]
    similarity = cosine_similarity(embeddings[indices])
    labels = [
        f"{topic}_{topic_names[topic]}"
        if topic in topic_names
        else f"{topic}_" + "_".join(word for word, _ in (topic_model.get_topic(topic) or [])[:3])
        for topic in selected.Topic
    ]
    fig = go.Figure(
        go.Heatmap(
            z=similarity[::-1],
            x=labels,
            y=labels[::-1],
            colorscale="YlGnBu",
            zmin=-1,
            zmax=1,
            colorbar=dict(title=dict(text="Kosinus-Ähnlichkeit", side="right")),
            hovertemplate="<b>Thema-X:</b> %{x}<br><b>Thema-Y:</b> %{y}<br>Ähnlichkeit: %{z:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis=dict(tickangle=90, automargin=True),
        yaxis=dict(automargin=True),
        height=700,
        margin=dict(l=150, r=30, t=30, b=100),
    )
    return fig
