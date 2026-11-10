"""Application assembly and static frontend hosting."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from server.routes import router
from server.settings import ROOT

app = FastAPI(title="BERTopic", version="0.3.0")
app.include_router(router)
if (ROOT / "dist").is_dir():
    app.mount("/", StaticFiles(directory=ROOT / "dist", html=True), name="frontend")
