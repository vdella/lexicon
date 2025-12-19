from __future__ import annotations

from fastapi import APIRouter
from backend.app.api.endpoints import regex

router = APIRouter()
router.include_router(regex.router, prefix="/regex", tags=["regex"])
