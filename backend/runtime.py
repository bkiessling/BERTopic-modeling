"""In-memory workspaces and serialized background jobs for local use."""

from __future__ import annotations
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache
from threading import RLock
from fastapi import HTTPException
import pandas as pd
from modules.analysis.state import AnalysisState
from modules.analysis.topic_naming import TopicNamingError
from modules.modeling.encoders import build_encoder

workers = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bertopic")
log = logging.getLogger(__name__)


def records(frame):
    return json.loads(frame.to_json(orient="records", force_ascii=False, date_format="iso"))


@dataclass
class Workspace:
    raw: pd.DataFrame | None = None
    file_name: str = ""
    cleaned: pd.DataFrame | None = None
    text_columns: list = field(default_factory=list)
    preprocessing: dict = field(default_factory=dict)
    cleaning_stats: dict = field(default_factory=dict)
    analysis: AnalysisState | None = None
    coordinates: object = None
    tsne_coordinates: object = None
    job: dict = field(
        default_factory=lambda: {
            "status": "idle",
            "progress": 0,
            "message": "",
            "error": "",
            "warning": "",
            "kind": "",
        }
    )
    touched: float = field(default_factory=time.time)
    lock: RLock = field(default_factory=RLock)


def workspace(token):
    with spaces_lock:
        state = spaces.get(token or "")
        if state is None:
            raise HTTPException(
                404,
                "Arbeitsbereich nicht mehr verfügbar. Bitte einen neuen Arbeitsbereich starten.",
            )
        state.touched = time.time()
        return state


def idle(state):
    if state.job["status"] in ("queued", "running"):
        raise HTTPException(409, "Bitte den laufenden Vorgang abwarten.")


def analysis_required(state):
    if state.analysis is None:
        raise HTTPException(409, "Bitte zuerst ein Modell trainieren.")
    return state.analysis


def run_job(state, kind, task):
    with state.lock:
        idle(state)
        state.job = {
            "status": "queued",
            "progress": 0,
            "message": "Wird vorbereitet …",
            "error": "",
            "warning": "",
            "kind": kind,
        }

    def report(percent, message):
        with state.lock:
            state.job.update(progress=percent, message=message)

    def execute():
        with state.lock:
            state.job["status"] = "running"
        try:
            warning = task(report)
        except (ValueError, TopicNamingError) as exc:
            with state.lock:
                state.job.update(
                    status="failed", error=str(exc), message="Vorgang nicht abgeschlossen"
                )
        except Exception:
            log.exception("Local workbench job failed")
            with state.lock:
                state.job.update(
                    status="failed",
                    error="Der Vorgang ist fehlgeschlagen. Serverprotokoll und Modellzugriff prüfen.",
                    message="Vorgang nicht abgeschlossen",
                )
        else:
            with state.lock:
                state.job.update(
                    status="completed", progress=100, message="Abgeschlossen", warning=warning or ""
                )

    initial = {
        "status": "queued",
        "progress": 0,
        "message": "Wird vorbereitet …",
        "error": "",
        "warning": "",
        "kind": kind,
    }
    workers.submit(execute)
    return initial


@lru_cache(maxsize=2)
def encoder(name):
    import torch

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    return build_encoder(name, device)


spaces: dict[str, Workspace] = {}
spaces_lock = RLock()
