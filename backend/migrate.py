"""One-time local secret migration; never overwrite configuration or print values."""

import os
from pathlib import Path
import shutil


def migrate_legacy_secrets(root: Path) -> bool:
    source = root / ".streamlit/secrets.toml"
    destination = root / "config/secrets.toml"
    if not source.is_file() or destination.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects an existing file even during simultaneous starts.
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as target, source.open("rb") as original:
            shutil.copyfileobj(original, target)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return True
