from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class RegexInput(BaseModel):
    regex: str = Field(..., min_length=0, description="User-facing regex string (surface syntax).")


class NormalizeResponse(BaseModel):
    regex: str
    normalized: str
    alphabet: List[str]


class SyntaxTreeNodeDTO(BaseModel):
    id: int
    value: str
    serial_number: Optional[int] = None
    left_id: Optional[int] = None
    right_id: Optional[int] = None

    nullable: bool
    first_pos: List[int]
    last_pos: List[int]
    follow_pos: List[int]


class SyntaxTreeResponse(BaseModel):
    regex: str
    normalized: str
    alphabet: List[str]
    root_id: int
    nodes: List[SyntaxTreeNodeDTO]


class TransitionDTO(BaseModel):
    src: str
    symbol: str
    dst: List[str]


class AutomatonResponse(BaseModel):
    kind: str = Field(default="DFA")
    states: List[str]
    alphabet: List[str]
    initial_state: str
    final_states: List[str]
    transitions: List[TransitionDTO]


class AutomatonInput(BaseModel):
    kind: str = Field(default="DFA")
    states: List[str]
    alphabet: List[str]
    initial_state: str
    final_states: List[str]
    transitions: List[TransitionDTO]
