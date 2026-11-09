import numpy as np
import pandas as pd
import plotly.express as px
from umap import UMAP
from sklearn.manifold import TSNE
from bertopic import BERTopic


def plot_topic_network(
    topic_model: BERTopic,
    topics: list[int],
    docs: list[str],
    embeddings,
    dim_reduction: str = "umap",
    top_n_legend: int | None = 20,
    width: int = 1000,
    height: int = 700,
):
    """Visualize topic network with legend labels and cluster centers labeled once."""

    if isinstance(embeddings, list):
        embeddings = np.asarray(embeddings)

    # Dimensionality reduction
    reducer = (
        UMAP(n_neighbors=10, n_components=2, min_dist=0.0, metric="cosine")
        if dim_reduction.lower() == "umap"
        else TSNE(n_components=2, perplexity=30, metric="cosine")
    )
    reduced = reducer.fit_transform(embeddings)

    # Topic info
    tinfo = topic_model.get_topic_info()
    label_map = dict(zip(tinfo.Topic, tinfo.Name))
    count_map = dict(zip(tinfo.Topic, tinfo.Count))

    # Create DataFrame for documents
    df = pd.DataFrame(reduced, columns=["x", "y"])
    df["topic"] = topics
    df["label"] = df["topic"].map(label_map)
    df["count"] = df["topic"].map(count_map)

    # Set color group for legend (e.g., "3_Klimawandel_Energie")
    df["color_group"] = df.apply(
        lambda row: "-1_outlier" if row.topic == -1 else f"{row.topic}_{row.label}",
        axis=1
    )

    # Custom color for outlier
    color_map = {"-1_outlier": "lightgrey"}

    # Define legend order: outlier first, then by topic number
    legend_order = ["-1_outlier"] + sorted(
        [cg for cg in df["color_group"].unique() if cg != "-1_outlier"],
        key=lambda x: int(x.split("_")[0])
    )

    # Scatter plot of all documents
    fig = px.scatter(
        df,
        x="x",
        y="y",
        color="color_group",
        color_discrete_map=color_map,
        opacity=0.6,
        hover_data={"topic": True, "label": True, "x": False, "y": False, "color_group": False},
        category_orders={"color_group": legend_order},
        width=width,
        height=height,
    )

    fig.update_layout(
        plot_bgcolor="white",
        xaxis_visible=False,
        yaxis_visible=False,
        legend=dict(itemsizing="constant", traceorder="normal"),
    )

    # Optionally hide topics not in top-n
    if top_n_legend is not None:
        top_labels = (
            tinfo[tinfo.Topic != -1]
            .nlargest(top_n_legend, "Count")
            .apply(lambda row: f"{row.Topic}_{row.Name}", axis=1)
            .tolist()
        )
        fig.for_each_trace(
            lambda tr: tr.update(visible="legendonly")
            if tr.name not in top_labels and tr.name != "-1_outlier"
            else tr.update(visible=True)
        )

    return fig
