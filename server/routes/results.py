"""Results HTTP endpoints."""

from __future__ import annotations
import json
from typing import Annotated
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
import pandas as pd
import plotly.express as px
from server.runtime import workspace, analysis_required, run_job, records, idle
from server.settings import key_binding
from server.schemas import (
    NamingRequest,
    OutlierRequest,
    TopicReductionRequest,
    TopicMergeRequest,
    TopicLabelRequest,
    TopicExclusionRequest,
)
from server.services.analysis.topic_table import build_topic_table, compute_topic_stats
from server.services.analysis.document_table import build_document_table
from server.services.analysis.export import build_result_archive
from server.services.analysis.topic_naming import name_topics, topic_keywords
from server.services.viz.topic_similarity import plot_topic_similarity
from server.services.viz.bar_chart import _plot_barcharts
from server.services.viz.projection import project_documents
from server.services.viz.colors import topic_colors

router = APIRouter()


def structural_analysis(state):
    analysis = analysis_required(state)
    try:
        analysis.require_all_topics_visible()
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    return analysis


@router.get("/api/results")
def results(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    full_info = analysis.named_topic_info()
    info = full_info[~full_info.Topic.isin(analysis.excluded_topics)]
    indices = analysis.visible_indices()
    docs = [analysis.result.documents[index] for index in indices]
    n_topics, outliers, average = compute_topic_stats(info, docs)
    return {
        "topics": records(build_topic_table(info, docs, analysis.result.config.top_n_words)),
        "stats": {
            "topics": n_topics,
            "documents": len(docs),
            "unique_ids": len({analysis.ids[index] for index in indices}),
            "outliers": float(outliers),
            "average": average,
        },
        "parameters": analysis.result.config.to_dict(),
        "keywords": [
            {"id": topic, "keywords": words}
            for topic, words in topic_keywords(analysis.result.model).items()
            if topic not in analysis.excluded_topics
        ],
        "naming": analysis.naming_metadata,
        "naming_needs_refresh": bool(analysis.topics_needing_names - analysis.excluded_topics),
        "topic_reductions": analysis.topic_reductions,
        "topic_merges": analysis.topic_merges,
        "manual_topic_names": analysis.manual_topic_names,
        "excluded_topics": records(
            full_info[full_info.Topic.isin(analysis.excluded_topics)][
                ["Topic", "CustomName", "Count"]
            ]
        ),
        "can_restore": analysis.original_topics is not None,
    }


@router.get("/api/documents")
def documents(
    x_workspace_id: Annotated[str, Header()],
    page: int = 0,
    search: str = "",
    grouped: bool = False,
    topic: int | None = None,
    sort: str = "ID",
    descending: bool = False,
    representative: bool = False,
):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    frame = build_document_table(
        analysis.ids,
        analysis.result.documents,
        analysis.result.model.topics_,
        analysis.named_topic_info(),
        "Textbeitrag",
        "Textbeitrag",
    )
    names = dict(zip(analysis.named_topic_info().Topic, analysis.named_topic_info().CustomName))
    frame.insert(0, "Themenname", frame.Thema.map(names))
    frame = frame[~frame.Thema.isin(analysis.excluded_topics)]
    # BERTopic's representative documents are examples, not a confidence ranking.
    examples = analysis.result.model.representative_docs_ or {}
    frame["Repräsentativ"] = [
        text in examples.get(int(topic_id), [])
        for text, topic_id in zip(frame.Textbeitrag, frame.Thema)
    ]
    if topic is not None:
        frame = frame[frame.Thema == topic]
    if representative:
        frame = frame[frame["Repräsentativ"]]
    if search:
        mask = (
            frame.astype(str)
            .apply(lambda column: column.str.contains(search, case=False, regex=False))
            .any(axis=1)
        )
        frame = frame[mask]
    if grouped:
        frame = (
            frame.groupby("ID", sort=False, dropna=False)
            .agg(
                {
                    "Themenname": lambda values: " | ".join(dict.fromkeys(values)),
                    "Thema": lambda values: sorted(set(values)),
                    "Textbeitrag": lambda values: " | ".join(values),
                    "Keywords": lambda values: list(
                        dict.fromkeys(word for words in values for word in words)
                    ),
                    "Repräsentativ": "any",
                }
            )
            .reset_index()
        )
    leading = ["ID", "Thema", "Themenname", "Textbeitrag"]
    frame = frame[leading + [column for column in frame.columns if column not in leading]]
    if sort not in frame.columns:
        raise HTTPException(400, "Unbekannte Sortierspalte.")
    if sort in ("Keywords",) or (grouped and sort == "Thema"):
        frame = frame.sort_values(
            sort, key=lambda values: values.astype(str), ascending=not descending, kind="stable"
        )
    else:
        frame = frame.sort_values(sort, ascending=not descending, kind="stable")
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
    info = info[~info.Topic.isin(analysis.excluded_topics)]
    names = dict(zip(info.Topic, info.CustomName))
    if kind == "similarity":
        figure = plot_topic_similarity(
            model, topic_names=names, excluded_topics=analysis.excluded_topics
        )
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
        labels = [f"{topic} · {names[topic]}" for topic in selected]
        figure = _plot_barcharts(
            model,
            selected,
            labels,
            min(30, max(1, top_words)),
            1000,
            max(420, (100 + min(30, max(1, top_words)) * 26) * len(selected)),
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
        indices = analysis.visible_indices()
        points = pd.DataFrame(
            {
                "x": coords[indices, 0],
                "y": coords[indices, 1],
                "Thema": [labels[model.topics_[index]] for index in indices],
            }
        )
        colors = topic_colors(info.Topic.tolist())
        figure = px.scatter(
            points,
            x="x",
            y="y",
            color="Thema",
            opacity=0.8,
            color_discrete_map={labels[topic]: color for topic, color in colors.items()},
            category_orders={"Thema": [labels[topic] for topic in sorted(labels)]},
        )
        figure.update_traces(marker={"size": 7}, hovertemplate="%{fullData.name}<extra></extra>")
        if -1 in labels:
            figure.update_traces(visible="legendonly", selector={"name": labels[-1]})
        figure.update_layout(
            xaxis_visible=False, yaxis_visible=False, height=760, legend={"orientation": "h"}
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
    if not (state.openai_key or key_binding()[0]):
        raise HTTPException(400, "Kein OpenAI-API-Key vorhanden.")

    def task(report):
        report(20, "Benenne Themen anhand der Keywords …")
        labels = name_topics(
            {
                topic: words
                for topic, words in topic_keywords(analysis.result.model).items()
                if topic not in analysis.excluded_topics
            },
            analysis.result.config.language,
            (state.openai_key or key_binding()[0]),
            body.model,
        )
        analysis.set_topic_names(labels, body.model)

    return run_job(state, "naming", task)


@router.post("/api/topics/exclude")
def exclude(body: TopicExclusionRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        analysis = analysis_required(state)
        try:
            analysis.exclude_topics(body.topics)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
    return {"message": "Themen aus der Auswertung ausgeschlossen."}


@router.post("/api/topics/include-all")
def include_all(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        analysis_required(state).excluded_topics.clear()
    return {"message": "Alle Themen wieder eingeblendet."}


@router.post("/api/topics/label")
def set_label(body: TopicLabelRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        analysis = analysis_required(state)
        try:
            analysis.set_manual_topic_name(body.topic, body.label)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
    return {"message": "Themenname gespeichert."}


@router.post("/api/topics/merge")
def merge(body: TopicMergeRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = structural_analysis(state)
    try:
        analysis.validate_merge(body.topics)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None

    def task(report):
        report(20, "Führe ausgewählte Themen zusammen …")
        with state.lock:
            analysis.merge_topics(body.topics)
        return "Themen zusammengeführt. Der neuen Gruppe kann jetzt ein Name gegeben werden."

    return run_job(state, "merge", task)


@router.post("/api/topics/reduce")
def reduce_topics(body: TopicReductionRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = structural_analysis(state)
    current = len(set(analysis.result.model.topics_) - {-1})
    if body.target >= current:
        raise HTTPException(400, "Die Zielanzahl muss kleiner als die aktuelle Themenanzahl sein.")

    def task(report):
        report(20, "Fasse ähnliche Themen zusammen …")
        with state.lock:
            analysis.reduce_topics(body.target)
        return "Themen zusammengefasst. Die Themennamen können jetzt neu vergeben werden."

    return run_job(state, "reduction", task)


@router.post("/api/outliers")
def outliers(body: OutlierRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = structural_analysis(state)

    def task(report):
        report(20, "Ordne Outlier neu zu …")
        if not analysis.reduce_outliers(body.threshold):
            return "Keine Outlier vorhanden."

    return run_job(state, "outliers", task)


@router.post("/api/outliers/restore")
def restore(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = structural_analysis(state)

    def task(report):
        report(20, "Stelle ursprüngliche Zuordnungen wieder her …")
        if not analysis.restore_outliers():
            return "Keine ursprünglichen Zuordnungen gespeichert."

    return run_job(state, "restore", task)


@router.get("/api/export")
def export(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    indices = analysis.visible_indices()
    info = analysis.named_topic_info()
    content = build_result_archive(
        [analysis.result.documents[index] for index in indices],
        [analysis.ids[index] for index in indices],
        [analysis.result.model.topics_[index] for index in indices],
        info[~info.Topic.isin(analysis.excluded_topics)],
        analysis.result.config.to_dict(),
        {
            "trained_at": analysis.trained_at,
            "text_columns": analysis.text_columns,
            "preprocessing": analysis.preprocessing,
            "outlier_thresholds": analysis.outlier_thresholds,
            "topic_naming": analysis.naming_metadata,
            "topic_reductions": analysis.topic_reductions,
            "topic_merges": analysis.topic_merges,
            "manual_topic_names": {
                topic: label
                for topic, label in analysis.manual_topic_names.items()
                if topic not in analysis.excluded_topics
            },
            "excluded_topics": sorted(analysis.excluded_topics),
            "source_document_count": len(analysis.result.documents),
        },
    )
    return Response(
        content,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="topic-modeling-results.zip"'},
    )
