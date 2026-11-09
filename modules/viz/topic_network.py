import numpy as np
import pandas as pd
import plotly.express as px
from modules.viz.projection import project_documents
import streamlit as st


def plot_topic_network(
    topic_model,
    topics: list[int],
    docs: list[str],
    embeddings,
    dim_reduction: str = "umap",
    top_n_legend: int | None = 20,
    width: int = 1000,
    height: int = 700,
    topic_names=None,
):
    """Visualize topic network with legend labels and cluster centers labeled once."""

    embeddings = np.asarray(embeddings, dtype=float)
    if embeddings.ndim != 2 or len(embeddings) != len(topics) or len(docs) != len(topics):
        raise ValueError("Dokumente, Themen und Embeddings müssen gleich viele Zeilen haben.")
    if not np.isfinite(embeddings).all():
        raise ValueError("Embeddings enthalten ungültige Werte.")
    if len(docs) == 0:
        fig = px.scatter()
        fig.add_annotation(text="Keine Dokumente vorhanden.", showarrow=False)
        return fig
    reduced = project_documents(embeddings, dim_reduction)

    # Topic info
    tinfo = topic_model.get_topic_info()
    label_map = dict(zip(tinfo.Topic, tinfo.Name))
    label_map.update({topic: f"{topic}_{label}" for topic, label in (topic_names or {}).items()})
    count_map = dict(zip(tinfo.Topic, tinfo.Count))

    # Create DataFrame for documents
    df = pd.DataFrame(reduced, columns=["x", "y"])
    df["topic"] = topics
    df["label"] = df["topic"].map(label_map)
    df["count"] = df["topic"].map(count_map)

    # Set color group for legend (e.g., "3_Klimawandel_Energie")
    df["color_group"] = df.apply(
        lambda row: "-1_outlier" if row.topic == -1 else row.label,
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
        top_labels = [label_map[topic] for topic in tinfo[tinfo.Topic != -1].nlargest(top_n_legend, "Count").Topic]
        fig.for_each_trace(
            lambda tr: tr.update(visible="legendonly")
            if tr.name not in top_labels and tr.name != "-1_outlier"
            else tr.update(visible=True)
        )

    return fig


project_documents = st.cache_data(show_spinner=False, max_entries=8)(project_documents)
