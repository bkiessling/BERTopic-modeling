"""Server-only configuration and credentials. Values never go to React."""

import os
from pathlib import Path
import tomllib
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]


def key_binding():
    for path in (
        ROOT / "config/secrets.toml",
        Path.home() / ".config/bertopic-workbench/secrets.toml",
    ):
        if not path.is_file():
            continue
        try:
            with path.open("rb") as source:
                values = tomllib.load(source)
        except (OSError, tomllib.TOMLDecodeError):
            raise HTTPException(
                400, "Server-Secrets konnten nicht gelesen werden. TOML-Syntax prüfen."
            ) from None
        for name in ("BERTOPIC_OPENAI_API_KEY", "OPENAI_API_KEY"):
            if str(values.get(name, "")).strip():
                return str(values[name]).strip(), f"Server-Secrets · {name}"
    for name in ("BERTOPIC_OPENAI_API_KEY", "OPENAI_API_KEY"):
        if os.environ.get(name, "").strip():
            return os.environ[name].strip(), f"Umgebungsvariable · {name}"
    return "", ""
