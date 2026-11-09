"""Modeling HTTP endpoints."""

from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Header, HTTPException
from backend.runtime import workspace, idle, run_job, encoder
from backend.settings import key_binding
from backend.schemas import TrainRequest, WebVectorizer
from modules.modeling.configuration import MODEL_OPTIONS, TrainingConfig
from modules.modeling.train_model import train_bertopic_model
from modules.analysis.state import AnalysisState
from modules.analysis.topic_naming import name_topics, topic_keywords, TopicNamingError
from modules.viz.projection import project_documents

router = APIRouter()


@router.post("/api/train")
def train(body: TrainRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        if state.cleaned is None:
            raise HTTPException(409, "Bitte zuerst Texte bereinigen.")
        try:
            params = dict(body.params)
            params["vectorizer"] = WebVectorizer.model_validate(params["vectorizer"]).model_dump()
            config = TrainingConfig.from_dict(params)
            errors = config.validate(state.cleaned.text.tolist())
        except (TypeError, KeyError, AttributeError, ValueError):
            raise HTTPException(400, "Unvollständige Modellparameter.") from None
        if config.embedding_model not in MODEL_OPTIONS:
            errors.append("Ein Modell aus der Auswahlliste verwenden.")
        if config.name_topics and not key_binding()[0]:
            errors.append("Für die KI-Benennung fehlt ein OpenAI-API-Key.")
        if errors:
            raise HTTPException(400, "\n".join(errors))
        data = state.cleaned.copy()

    def task(report):
        report(1, "Lade Embedding-Modell …")
        result = train_bertopic_model(
            data.text.tolist(),
            config,
            encoder(config.embedding_model),
            on_progress=lambda p, m: report(min(p, 90), m),
        )
        analysis = AnalysisState(result, data.id.tolist(), state.text_columns, state.preprocessing)
        warning = ""
        if config.name_topics:
            report(92, "Benenne Themen anhand der Keywords …")
            try:
                labels = name_topics(
                    topic_keywords(result.model),
                    config.language,
                    key_binding()[0],
                    config.naming_model,
                )
                analysis.set_topic_names(labels, config.naming_model)
            except TopicNamingError as exc:
                warning = str(exc)
        report(95, "Bereite Dokumentenkarte vor …")
        coordinates = project_documents(result.embeddings)
        with state.lock:
            state.analysis, state.coordinates, state.tsne_coordinates = analysis, coordinates, None
        return warning

    return run_job(state, "training", task)


@router.get("/api/job")
def get_job(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        return dict(state.job)
