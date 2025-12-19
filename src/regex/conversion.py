"""
Regex -> DFA conversion using the syntax-tree direct construction (Aho-Sethi-Ullman).

Key cleanups vs the original:
- uses frozenset[int] of position serials as DFA state identity (no substring bugs)
- sets the initial state deterministically (not conditionally)
- does not generate transitions for epsilon ('&') or the end-marker ('#') as input symbols
"""
from __future__ import annotations

from collections import deque
from typing import Dict, FrozenSet, Set

from src.regex.syntax_tree import SyntaxTree
from src.automata.structures import FiniteAutomata, State


PosSet = FrozenSet[int]


def fa_from(regex: str) -> FiniteAutomata:
    """Build a deterministic finite automaton for `regex`."""
    tree = SyntaxTree(regex)
    tree.root.calculate_follow_pos()

    # Map serial_number -> leaf Node
    by_pos = {n.serial_number: n for n in tree.nodes if n.serial_number is not None}

    end_pos = tree.end_marker_position()

    def make_state(posset: PosSet) -> State:
        # Stable label, deterministic ordering
        label = "{" + ",".join(str(p) for p in sorted(posset)) + "}"
        return State(label)

    dfa = FiniteAutomata()
    dfa.alphabet = set(tree.alphabet)

    # Initial DFA state is firstpos(root) as position serials
    start_positions: PosSet = frozenset(n.serial_number for n in tree.root.first_pos if n.serial_number is not None)
    start_state = make_state(start_positions)

    dfa.states.add(start_state)
    dfa.initial_state = start_state
    if end_pos in start_positions:
        dfa.final_states.add(start_state)

    # Determinize using a work queue of position sets
    state_by_pos: Dict[PosSet, State] = {start_positions: start_state}
    queue = deque([start_positions])

    while queue:
        current = queue.popleft()
        current_state = state_by_pos[current]

        for symbol in dfa.alphabet:
            next_positions: Set[int] = set()

            for pos in current:
                node = by_pos[pos]
                if node.value == symbol:
                    next_positions |= {n.serial_number for n in node.follow_pos if n.serial_number is not None}

            if not next_positions:
                continue  # No transition on this symbol.

            nxt: PosSet = frozenset(next_positions)
            if nxt not in state_by_pos:
                nxt_state = make_state(nxt)
                state_by_pos[nxt] = nxt_state
                dfa.states.add(nxt_state)
                if end_pos in nxt:
                    dfa.final_states.add(nxt_state)
                queue.append(nxt)

            dfa.transitions[(current_state, symbol)] = {state_by_pos[nxt]}

    return dfa


if __name__ == "__main__":
    fa = fa_from("b?(ab)*a?")
    print(fa)
