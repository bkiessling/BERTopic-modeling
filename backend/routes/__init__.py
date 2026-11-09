"""Compose feature routes without owning application state."""

from fastapi import APIRouter
from backend.routes import system, imports, modeling, results

router = APIRouter()
for feature in (system, imports, modeling, results):
    router.include_router(feature.router)
