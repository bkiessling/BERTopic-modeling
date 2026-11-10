"""Local application entry point: python -m server."""

import argparse
import socket
import uvicorn
from server.settings import ROOT
from server.migrate import migrate_legacy_secrets


def main():
    parser = argparse.ArgumentParser(description="Topic Modeling – lokale Themenanalyse")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port muss zwischen 1 und 65535 liegen.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", args.port))
        except OSError:
            parser.error(
                f"Port {args.port} ist bereits belegt. Der alte Server läuft noch. Beenden oder mit --port {args.port + 1 if args.port < 65535 else 8001} starten."
            )
    if not (ROOT / "dist/index.html").is_file():
        parser.error("Frontend fehlt. Zuerst npm ci und npm run build ausführen.")
    if migrate_legacy_secrets(ROOT):
        print(
            "Lokale Secrets nach config/secrets.toml übernommen. Die bisherige Datei bleibt unverändert."
        )
    uvicorn.run("server.app:app", host="127.0.0.1", port=args.port, workers=1)


if __name__ == "__main__":
    main()
