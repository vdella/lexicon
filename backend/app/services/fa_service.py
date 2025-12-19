from __future__ import annotations

from typing import Dict, Set, Tuple

from fastapi import HTTPException

from src.automata.structures import FiniteAutomata, State
from backend.app.schemas.models import AutomatonInput


def deserialize_automaton(payload: AutomatonInput) -> FiniteAutomata:
    """Deserialize an AutomatonInput (JSON) back into FiniteAutomata.

    Notes:
    - transitions can be NFA-like (dst list), but we still store them as sets.
    - This does not attempt to validate DFA-ness (one dst per (state,symbol)).
    """
    dfa = FiniteAutomata()

    # Build State instances
    state_by_label: Dict[str, State] = {label: State(label) for label in payload.states}
    dfa.states = set(state_by_label.values())
    dfa.alphabet = set(payload.alphabet)

    if payload.initial_state not in state_by_label:
        raise HTTPException(status_code=400, detail="initial_state is not in states.")
    dfa.initial_state = state_by_label[payload.initial_state]

    for f in payload.final_states:
        if f not in state_by_label:
            raise HTTPException(status_code=400, detail=f"final state {f!r} is not in states.")
        dfa.final_states.add(state_by_label[f])

    for t in payload.transitions:
        if t.src not in state_by_label:
            raise HTTPException(status_code=400, detail=f"transition src {t.src!r} is not in states.")
        if t.symbol not in dfa.alphabet:
            raise HTTPException(status_code=400, detail=f"transition symbol {t.symbol!r} is not in alphabet.")
        for d in t.dst:
            if d not in state_by_label:
                raise HTTPException(status_code=400, detail=f"transition dst {d!r} is not in states.")
        dfa.transitions[(state_by_label[t.src], t.symbol)] = {state_by_label[d] for d in t.dst}

    return dfa
