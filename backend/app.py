"""Application assembly and static frontend hosting."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routes import router
from backend.settings import ROOT

app = FastAPI(title="BERTopic", version="0.2.0")
app.include_router(router)
if (ROOT / "frontend/dist").is_dir():
    app.mount("/", StaticFiles(directory=ROOT / "frontend/dist", html=True), name="frontend")
