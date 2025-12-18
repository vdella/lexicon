from dataclasses import dataclass, field
from typing import Set, Dict, Tuple


@dataclass
class FiniteAutomata:
    initial_state: "State" = field(init=False)
    states: Set["State"] = field(default_factory=set)
    transitions: Dict[Tuple["State", "State"], "State"] = field(default_factory=dict)
    final_states: Set["State"] = field(default_factory=set)


@dataclass(frozen=True)
class State:
    label: str = None

    def __repr__(self):
        return self.label


if __name__ == '__main__':
    fa = FiniteAutomata(State("A"))
    print(fa.states)
