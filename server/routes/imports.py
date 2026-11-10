"""Imports HTTP endpoints."""

from __future__ import annotations
import io
import zipfile
from typing import Annotated
from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
import pandas as pd
from server.runtime import workspace, idle, records
from server.schemas import CleanRequest
from server.services.upload.delimiter_utils import detect_delimiter
from server.services.preprocessing.text_selection import build_text_df
from server.services.preprocessing.text_cleaner import clean_text_column, filter_text_column
from server.services.modeling.configuration import get_default_params

router = APIRouter()


@router.post("/api/import")
def import_file(
    x_workspace_id: Annotated[str, Header()],
    file: UploadFile = File(...),
    delimiter: str | None = Form(None),
):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        content = file.file.read(25 * 1024 * 1024 + 1)
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(413, "Datei ist größer als 25 MB.")
        try:
            if (file.filename or "").lower().endswith(".csv"):
                text = content.decode("utf-8-sig")
                sep = delimiter or detect_delimiter(text)
                if sep not in (",", ";", "\t"):
                    sep = ","
                frame = pd.read_csv(io.StringIO(text), sep=sep)
            elif (file.filename or "").lower().endswith(".xlsx"):
                frame = pd.read_excel(io.BytesIO(content))
                sep = None
            else:
                raise HTTPException(400, "Bitte eine CSV- oder XLSX-Datei auswählen.")
        except (ValueError, UnicodeError, OSError, zipfile.BadZipFile):
            raise HTTPException(
                400,
                "Datei konnte nicht gelesen werden. UTF-8, Dateiformat und Trennzeichen prüfen.",
            ) from None
        if frame.empty:
            raise HTTPException(400, "Die Datei enthält keine Datenzeilen.")
        frame.columns = frame.columns.map(str)
        if not frame.columns.is_unique:
            raise HTTPException(400, "Spaltennamen müssen eindeutig sein.")
        state.raw, state.file_name = frame, file.filename or "Upload"
        state.cleaned, state.analysis, state.coordinates, state.tsne_coordinates = (
            None,
            None,
            None,
            None,
        )
    return {
        "file_name": state.file_name,
        "rows": len(frame),
        "columns": frame.columns.tolist(),
        "text_columns": frame.select_dtypes(include=["object", "string"]).columns.tolist(),
        "delimiter": sep,
        "preview": records(frame.head(8)),
    }


@router.post("/api/clean")
def clean(body: CleanRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        if state.raw is None:
            raise HTTPException(409, "Bitte zuerst eine Datei importieren.")
        if (
            not body.text_columns
            or len(set(body.text_columns)) != len(body.text_columns)
            or any(col not in state.raw.columns for col in body.text_columns)
        ):
            raise HTTPException(400, "Mindestens eine gültige Textspalte auswählen.")
        if body.id_column != "ID generieren" and (
            body.id_column not in state.raw.columns or body.id_column in body.text_columns
        ):
            raise HTTPException(
                400, "ID-Spalte muss vorhanden und von den Textspalten verschieden sein."
            )
        selected = build_text_df(state.raw, body.text_columns, body.id_column)
        if body.sample_percentage < 100:
            selected = selected.sample(
                frac=body.sample_percentage / 100, random_state=42
            ).reset_index(drop=True)
        frame = filter_text_column(clean_text_column(selected, "text"), "text")
        words = {word.strip().lower() for word in body.custom_stopwords.split(",") if word.strip()}
        if words:
            # Exact token/phrase matching, including start/end of text.
            for word in words:
                import re

                frame["text"] = frame.text.str.replace(
                    r"(?<!\w)" + re.escape(word) + r"(?!\w)", " ", regex=True
                )
            frame["text"] = frame.text.str.replace(r"\s+", " ", regex=True).str.strip()
            frame = filter_text_column(frame, "text")
        if frame.empty:
            raise HTTPException(400, "Nach der Bereinigung sind keine Texte übrig.")
        if frame.id.isna().any():
            raise HTTPException(
                400,
                "Die ID-Spalte enthält fehlende Werte. IDs generieren oder eine vollständige Spalte wählen.",
            )
        state.cleaned, state.analysis, state.coordinates, state.tsne_coordinates = (
            frame.reset_index(drop=True),
            None,
            None,
            None,
        )
        state.text_columns, state.preprocessing = body.text_columns, body.model_dump()
        state.cleaning_stats = {"rows_before": len(selected)}
    return {
        "rows_before": len(selected),
        "rows": len(frame),
        "average_length": round(float(frame.text.str.len().mean()), 1),
        "preview": records(frame.head(8)),
        "defaults": get_default_params(len(frame), float(frame.text.str.len().mean())),
    }
