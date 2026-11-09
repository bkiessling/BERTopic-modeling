"""Results HTTP endpoints."""

from __future__ import annotations
import json
from typing import Annotated
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
import pandas as pd
import plotly.express as px
from backend.runtime import workspace, analysis_required, run_job, records
from backend.settings import key_binding
from backend.schemas import NamingRequest, OutlierRequest
from modules.analysis.topic_table import build_topic_table, compute_topic_stats
from modules.analysis.document_table import build_document_table
from modules.analysis.export import build_result_archive
from modules.analysis.topic_naming import name_topics, topic_keywords
from modules.viz.topic_similarity import plot_topic_similarity
from modules.viz.bar_chart import _plot_barcharts
from modules.viz.projection import project_documents

router = APIRouter()


@router.get("/api/results")
def results(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    info, docs = analysis.named_topic_info(), analysis.result.documents
    n_topics, outliers, average = compute_topic_stats(info, docs)
    return {
        "topics": records(build_topic_table(info, docs, analysis.result.config.top_n_words)),
        "stats": {
            "topics": n_topics,
            "documents": len(docs),
            "unique_ids": len(set(analysis.ids)),
            "outliers": float(outliers),
            "average": average,
        },
        "parameters": analysis.result.config.to_dict(),
        "keywords": [
            {"id": topic, "keywords": words}
            for topic, words in topic_keywords(analysis.result.model).items()
        ],
        "naming": analysis.naming_metadata,
        "can_restore": analysis.original_topics is not None,
    }


@router.get("/api/documents")
def documents(
    x_workspace_id: Annotated[str, Header()], page: int = 0, search: str = "", grouped: bool = False
):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    frame = build_document_table(
        analysis.ids,
        analysis.result.documents,
        analysis.result.model.topics_,
        analysis.named_topic_info(),
        "Textbeitrag",
        "ID" if grouped else "Textbeitrag",
    )
    if search:
        mask = (
            frame.astype(str)
            .apply(lambda column: column.str.contains(search, case=False, regex=False))
            .any(axis=1)
        )
        frame = frame[mask]
    page = max(0, page)
    return {
        "rows": records(frame.iloc[page * 50 : (page + 1) * 50]),
        "total": len(frame),
        "page": page,
        "page_size": 50,
    }


@router.get("/api/charts/{kind}")
def chart(
    kind: str,
    x_workspace_id: Annotated[str, Header()],
    topics: str = "",
    top_words: int = 5,
    method: str = "umap",
):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    model = analysis.result.model
    info = analysis.named_topic_info()
    names = analysis.topic_names
    if kind == "similarity":
        figure = plot_topic_similarity(model, topic_names=names)
    elif kind == "bars":
        try:
            selected = (
                [int(topic) for topic in topics.split(",") if topic]
                if topics
                else info[info.Topic != -1].nlargest(4, "Count").Topic.tolist()
            )
        except ValueError:
            raise HTTPException(400, "Ungültige Themenauswahl.") from None
        if not 1 <= len(selected) <= 4 or any(
            topic not in info.Topic.tolist() or topic == -1 for topic in selected
        ):
            raise HTTPException(400, "Ein bis vier vorhandene Themen auswählen.")
        labels = [
            f"{topic} · {names.get(topic, model.get_topic_info().set_index('Topic').loc[topic, 'Name'])}"
            for topic in selected
        ]
        figure = _plot_barcharts(
            model, selected, labels, min(30, max(1, top_words)), 1000, 280 * len(selected)
        )
    elif kind == "network":
        coords = state.coordinates
        if method == "tsne":
            with state.lock:
                if state.tsne_coordinates is None:
                    state.tsne_coordinates = project_documents(analysis.result.embeddings, "tsne")
                coords = state.tsne_coordinates
        elif method != "umap":
            raise HTTPException(400, "Unbekannte Projektion.")
        labels = {
            int(row.Topic): f"{int(row.Topic)} · {names.get(int(row.Topic), row.Name)}"
            for row in info.itertuples()
        }
        points = pd.DataFrame(
            {
                "x": coords[:, 0],
                "y": coords[:, 1],
                "Thema": [labels[topic] for topic in model.topics_],
            }
        )
        figure = px.scatter(
            points,
            x="x",
            y="y",
            color="Thema",
            opacity=0.7,
            color_discrete_sequence=[
                "#7560dd",
                "#56a998",
                "#dbab67",
                "#e48599",
                "#6d99cd",
                "#a68ac8",
            ],
        )
        figure.update_traces(marker={"size": 7}, hovertemplate="%{fullData.name}<extra></extra>")
        figure.update_layout(
            xaxis_visible=False, yaxis_visible=False, height=540, legend={"orientation": "h"}
        )
    else:
        raise HTTPException(404, "Diagramm nicht gefunden.")
    figure.update_layout(
        font={"family": "Inter, ui-sans-serif, system-ui", "color": "#424650"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 40, "r": 20, "t": 45, "b": 60},
    )
    return json.loads(figure.to_json())


@router.post("/api/name")
def name(body: NamingRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    if not key_binding()[0]:
        raise HTTPException(400, "Kein OpenAI-API-Key vorhanden.")

    def task(report):
        report(20, "Benenne Themen anhand der Keywords …")
        labels = name_topics(
            topic_keywords(analysis.result.model),
            analysis.result.config.language,
            key_binding()[0],
            body.model,
        )
        analysis.set_topic_names(labels, body.model)

    return run_job(state, "naming", task)


@router.post("/api/outliers")
def outliers(body: OutlierRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)

    def task(report):
        report(20, "Ordne Ausreißer neu zu …")
        if not analysis.reduce_outliers(body.threshold):
            return "Keine Ausreißer vorhanden."

    return run_job(state, "outliers", task)


@router.post("/api/outliers/restore")
def restore(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)

    def task(report):
        report(20, "Stelle ursprüngliche Zuordnungen wieder her …")
        if not analysis.restore_outliers():
            return "Keine ursprünglichen Zuordnungen gespeichert."

    return run_job(state, "restore", task)


@router.get("/api/export")
def export(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    content = build_result_archive(
        analysis.result.documents,
        analysis.ids,
        analysis.result.model.topics_,
        analysis.named_topic_info(),
        analysis.result.config.to_dict(),
        {
            "trained_at": analysis.trained_at,
            "text_columns": analysis.text_columns,
            "preprocessing": analysis.preprocessing,
            "outlier_thresholds": analysis.outlier_thresholds,
            "topic_naming": analysis.naming_metadata,
        },
    )
    return Response(
        content,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="bertopic-results.zip"'},
    )
