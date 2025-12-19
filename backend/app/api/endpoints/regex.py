from __future__ import annotations

from fastapi import APIRouter, HTTPException
from backend.app.services.schemas import (
    RegexAnalyzeRequest,
    RegexAnalyzeResponse,
    RegexFigureRequest,
    RegexFigureResponse,
)
from backend.app.services import rosetta
from src.regex.sanitization import validate
from src.regex.syntax_tree import SyntaxTree

router = APIRouter()


@router.post("/analyze", response_model=RegexAnalyzeResponse)
def analyze(req: RegexAnalyzeRequest):
    try:
        validate(req.regex)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return rosetta.analyze(req.regex, active_page=req.active_page)


@router.post("/figure", response_model=RegexFigureResponse)
def figure(req: RegexFigureRequest):
    try:
        validate(req.regex)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    tree = SyntaxTree(req.regex)
    tree.root.calculate_follow_pos()
    fig = rosetta.build_plotly_figure(tree, active_page=req.active_page)
    return {"figure": fig}
