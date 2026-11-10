"""Deterministic offline server, used only by browser tests."""

import importlib
import numpy as np
from bertopic.backend import BaseEmbedder
import uvicorn

backend = importlib.import_module("server.routes.modeling")


class OfflineEncoder(BaseEmbedder):
    def encode(self, documents, **kwargs):
        rng = np.random.default_rng(42)
        return np.asarray(
            [
                np.eye(3)[0 if "katze" in doc else 1 if "fussball" in doc else 2]
                + rng.normal(0, 0.03, 3)
                for doc in documents
            ]
        )


backend.encoder = lambda name: OfflineEncoder()
from server.app import app

backend.key_binding = lambda: ("", "")
importlib.import_module("server.routes.system").key_binding = lambda: ("", "")
importlib.import_module("server.routes.results").key_binding = lambda: ("", "")
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
