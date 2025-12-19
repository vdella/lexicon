from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, Optional


@dataclass
class FiniteAutomata:
    """
    Deterministic Finite Automaton (DFA).

    transitions:
        (state, symbol) -> set of states
        (singleton sets for DFA, but NFA-compatible by design)
    """
    states: Set["State"] = field(default_factory=set)
    alphabet: Set[str] = field(default_factory=set)
    transitions: Dict[Tuple["State", str], Set["State"]] = field(default_factory=dict)
    initial_state: Optional["State"] = None
    final_states: Set["State"] = field(default_factory=set)

    def add_state(self, state: "State", *, initial=False, final=False) -> None:
        self.states.add(state)
        if initial:
            self.initial_state = state
        if final:
            self.final_states.add(state)

    def add_transition(self, src: "State", symbol: str, dst: "State") -> None:
        self.states.add(src)
        self.states.add(dst)
        self.alphabet.add(symbol)
        self.transitions.setdefault((src, symbol), set()).add(dst)


@dataclass(frozen=True)
class State:
    """
    Automaton state.

    Identity is defined solely by its label.
    """
    label: str

    def __repr__(self) -> str:
        return self.label
