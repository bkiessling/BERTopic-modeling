"""System HTTP endpoints."""

from __future__ import annotations
import secrets
import time
from typing import Annotated
from fastapi import APIRouter, Header, HTTPException
from server.runtime import Workspace, spaces, spaces_lock, workspace, records
from server.settings import key_binding
from server.schemas import NamingRequest, SessionKeyRequest
from server.services.modeling.configuration import MODEL_OPTIONS, get_default_params
from server.services.analysis.topic_naming import (
    NAMING_MODELS,
    DEFAULT_NAMING_MODEL,
    check_model_access,
    TopicNamingError,
)

router = APIRouter()


@router.get("/api/health")
def health():
    return {"status": "ok", "api_contract": "bertopic-proportions-v1"}


@router.get("/api/capabilities")
def capabilities(x_workspace_id: Annotated[str | None, Header()] = None):
    key, source = key_binding()
    if x_workspace_id and workspace(x_workspace_id).openai_key:
        key, source = workspace(x_workspace_id).openai_key, "Aktueller Arbeitsbereich"
    return {
        "models": [
            {
                "id": name,
                "label": option.label,
                "languages": option.languages,
                "description": option.description,
            }
            for name, option in MODEL_OPTIONS.items()
        ],
        "naming_models": NAMING_MODELS,
        "key_present": bool(key),
        "key_source": source,
        "default_naming_model": DEFAULT_NAMING_MODEL,
    }


@router.post("/api/workspaces")
def create_workspace():
    with spaces_lock:
        expired = [
            token
            for token, state in spaces.items()
            if time.time() - state.touched > 7200
            and state.job["status"] not in ("queued", "running")
        ]
        for token in expired:
            del spaces[token]
        if len(spaces) >= 20:
            raise HTTPException(
                429,
                "Zu viele lokale Arbeitsbereiche geöffnet. Server neu starten oder alte Sitzungen auslaufen lassen.",
            )
        token = secrets.token_urlsafe(32)
        spaces[token] = Workspace()
    return {"id": token}


@router.get("/api/workspace")
def get_workspace(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    imported = (
        None
        if state.raw is None
        else {
            "file_name": state.file_name,
            "rows": len(state.raw),
            "columns": state.raw.columns.tolist(),
            "text_columns": state.raw.select_dtypes(include=["object", "string"]).columns.tolist(),
            "delimiter": None,
            "preview": records(state.raw.head(8)),
        }
    )
    cleaned = (
        None
        if state.cleaned is None
        else {
            "rows": len(state.cleaned),
            "rows_before": state.cleaning_stats.get("rows_before", len(state.cleaned)),
            "average_length": round(float(state.cleaned.text.str.len().mean()), 1),
            "preview": records(state.cleaned.head(8)),
            "defaults": get_default_params(
                len(state.cleaned), float(state.cleaned.text.str.len().mean())
            ),
        }
    )
    return {
        "file_name": state.file_name,
        "imported": state.raw is not None,
        "cleaned": state.cleaned is not None,
        "has_results": state.analysis is not None,
        "job": dict(state.job),
        "import_result": imported,
        "clean_result": cleaned,
        "text_columns": state.text_columns,
        "id_column": state.preprocessing.get("id_column", "ID generieren"),
        "preprocessing": state.preprocessing,
    }


@router.post("/api/openai/check")
def check_openai(body: NamingRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    try:
        check_model_access(state.openai_key or key_binding()[0], body.model)
    except TopicNamingError as exc:
        raise HTTPException(400, str(exc)) from None
    return {
        "message": "Key akzeptiert; Modell sichtbar. Responses-Berechtigung und Guthaben werden beim Benennen geprüft."
    }


@router.post("/api/openai/key")
def set_session_key(body: SessionKeyRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    key = body.key.get_secret_value().strip()
    if not key or len(key) > 512 or any(c.isspace() for c in key):
        raise HTTPException(400, "Bitte einen vollständigen API-Key ohne Leerzeichen eingeben.")
    with state.lock:
        state.openai_key = key
    return {"key_present": True, "key_source": "Aktueller Arbeitsbereich"}
