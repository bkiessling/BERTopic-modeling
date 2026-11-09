import numpy as np
import plotly.graph_objects as go
from bertopic import BERTopic


def visualize_heatmap(topic_model: BERTopic, top_n_topics: int = 10, n_words: int = 10):
    """
    Create a Plotly heatmap of term importance per topic.

    Parameters:
    - topic_model (BERTopic): A trained BERTopic model.
    - top_n_topics (int): Number of top topics to visualize.
    - n_words (int): Number of top words per topic.

    Returns:
    - fig (go.Figure): Plotly figure object.
    """

    # Get top topics (excluding outliers -1)
    topic_info = topic_model.get_topic_info()
    top_topics = topic_info[topic_info.Topic != -1].head(top_n_topics)["Topic"].tolist()

    # Collect unique top words across selected topics
    words = []
    for topic in top_topics:
        topic_words = topic_model.get_topic(topic)[:n_words]
        words.extend([word for word, _ in topic_words])
    words = list(dict.fromkeys(words))  # Preserve order

    # Build the matrix of weights
    heatmap_values = []
    for topic in top_topics:
        topic_words = dict(topic_model.get_topic(topic))
        row = [topic_words.get(word, 0) for word in words]
        heatmap_values.append(row)

    # Generate Plotly heatmap
    fig = go.Figure(data=go.Heatmap(
        z=np.array(heatmap_values),
        x=words,
        y=[f"Thema {t}" for t in top_topics],
        colorscale="Blues",
        colorbar=dict(title="Wortgewichtung"),
        hoverongaps=False
    ))

    fig.update_layout(
        title="Heatmap der Wortgewichtung pro Thema",
        xaxis_title="Begriffe",
        yaxis_title="Themen",
        height=400 + 30 * len(top_topics),
        margin=dict(t=60, l=120, r=30, b=100),
        xaxis=dict(tickangle=45)
    )

    return fig
