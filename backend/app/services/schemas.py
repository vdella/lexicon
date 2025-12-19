from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RegexAnalyzeRequest(BaseModel):
    regex: str = Field(..., description="User regex without end-marker '#'.")
    active_page: int = Field(0, ge=0, description="0 hides all node metadata; >0 reveals incrementally.")


class RegexFigureRequest(BaseModel):
    regex: str
    active_page: int = Field(..., ge=0)


class RegexAnalyzeResponse(BaseModel):
    regex: str
    page_quantity: int
    figure: Dict[str, Any]
    follow_pos_table: List[Dict[str, Any]]
    fa_table: List[Dict[str, str]]
    fa_dot: str
    fa_png: Optional[str] = None


class RegexFigureResponse(BaseModel):
    figure: Dict[str, Any]
