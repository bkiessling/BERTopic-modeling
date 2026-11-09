import numpy as np
import plotly.graph_objects as go
from sklearn.metrics.pairwise import cosine_similarity
from bertopic import BERTopic

def plot_topic_similarity(topic_model: BERTopic, top_n_topics: int = 20):
    # Extract topic embeddings
    topic_embeddings = topic_model.topic_embeddings_

    # Filter top N topics, skip outliers
    topic_info = topic_model.get_topic_info()
    topic_info = topic_info[topic_info.Topic != -1].head(top_n_topics)
    selected_topics = topic_info.Topic.tolist()

    # Create short labels from top 3 words
    labels = []
    for topic_id in selected_topics:
        words = topic_model.get_topic(topic_id)
        top_words = "_".join([word[0] for word in words[:3]])
        labels.append(f"{topic_id}_{top_words}")

    # Get topic indices and extract embeddings
    topic_all_info = topic_model.get_topic_info()
    indices = [topic_all_info.index[topic_all_info.Topic == topic].tolist()[0] for topic in selected_topics]
    selected_embeddings = topic_embeddings[indices]
    similarity_matrix = cosine_similarity(selected_embeddings)

    # Reverse for topic 0 on top
    reversed_labels = labels[::-1]
    reversed_matrix = similarity_matrix[::-1]

    fig = go.Figure(data=go.Heatmap(
        z=reversed_matrix,
        x=labels,
        y=reversed_labels,
        colorscale="YlGnBu",
        showscale=False,
        hovertemplate="<b>Thema-X:</b> %{x}<br><b>Thema-Y:</b> %{y}<br><b>Ähnlichkeit (z-Wert):</b> %{z:.2f}<extra></extra>",
        colorbar=dict(title="Ähnlichkeit", titleside="right")
    ))

    fig.update_layout(
        xaxis=dict(
            title="",
            tickangle=90,
            automargin=True
        ),
        yaxis=dict(
            automargin=True
        ),
        height=900,
        showlegend=False,
        margin=dict(l=150, r=30, t=30, b=100)
    )

    return fig
