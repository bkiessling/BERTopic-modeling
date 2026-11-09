"""Local application entry point: python -m backend."""

import argparse
import uvicorn
from backend.settings import ROOT
from backend.migrate import migrate_legacy_secrets


def main():
    parser = argparse.ArgumentParser(description="BERTopic – local topic modeling")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not (ROOT / "frontend/dist/index.html").is_file():
        parser.error(
            "Frontend fehlt. Zuerst npm --prefix frontend ci und npm --prefix frontend run build ausführen."
        )
    if migrate_legacy_secrets(ROOT):
        print(
            "Lokale Secrets nach config/secrets.toml übernommen. Die bisherige Datei bleibt unverändert."
        )
    uvicorn.run("backend.app:app", host="127.0.0.1", port=args.port, workers=1)


if __name__ == "__main__":
    main()
