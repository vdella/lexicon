from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

from src.regex.format import normalize
from src.regex.sanitization import validate
from src.regex.syntax_tree import SyntaxTree, Node
from src.regex.conversion import fa_from
from src.automata.structures import FiniteAutomata, State


def normalize_regex(regex: str) -> tuple[str, List[str]]:
    """Validate and normalize a surface regex string.

    Returns (normalized_expression, alphabet_list).
    """
    validate(regex)
    normalized = normalize(regex)
    return normalized.expression, sorted(normalized.alphabet)


def build_syntax_tree(regex: str) -> SyntaxTree:
    """Create a SyntaxTree (also validates and normalizes)."""
    return SyntaxTree(regex)


def regex_to_dfa(regex: str) -> FiniteAutomata:
    """Convert a surface regex to a DFA."""
    validate(regex)
    return fa_from(regex)


def serialize_dfa(dfa: FiniteAutomata) -> dict:
    """Serialize FiniteAutomata into JSON-friendly primitives."""
    states = sorted([s.label for s in dfa.states])
    alphabet = sorted(list(dfa.alphabet))
    initial = dfa.initial_state.label if dfa.initial_state else ""
    finals = sorted([s.label for s in dfa.final_states])

    transitions = []
    # transitions: (State, symbol) -> set[State]
    for (src, sym), dsts in dfa.transitions.items():
        transitions.append({
            "src": src.label,
            "symbol": sym,
            "dst": sorted([d.label for d in dsts]),
        })

    transitions.sort(key=lambda t: (t["src"], t["symbol"], ",".join(t["dst"])))
    return {
        "kind": "DFA",
        "states": states,
        "alphabet": alphabet,
        "initial_state": initial,
        "final_states": finals,
        "transitions": transitions,
    }


def serialize_syntax_tree(tree: SyntaxTree) -> dict:
    """Serialize SyntaxTree into a stable node list.

    Node ids are assigned by a pre-order traversal.
    first_pos/last_pos/follow_pos are represented by position serial numbers.
    """
    node_id: Dict[int, int] = {}
    nodes_out = []

    def get_id(n: Node) -> int:
        key = id(n)
        if key not in node_id:
            node_id[key] = len(node_id) + 1
        return node_id[key]

    def pos_list(nodes) -> List[int]:
        pos = []
        for p in nodes:
            if p.serial_number is not None:
                pos.append(p.serial_number)
        return sorted(set(pos))

    def visit(n: Node) -> None:
        nid = get_id(n)
        left_id = get_id(n.left) if n.left else None
        right_id = get_id(n.right) if n.right else None

        nodes_out.append({
            "id": nid,
            "value": n.value,
            "serial_number": n.serial_number,
            "left_id": left_id,
            "right_id": right_id,
            "nullable": bool(n.nullable),
            "first_pos": pos_list(n.first_pos),
            "last_pos": pos_list(n.last_pos),
            "follow_pos": pos_list(n.follow_pos),
        })
        if n.left:
            visit(n.left)
        if n.right:
            visit(n.right)

    visit(tree.root)
    # De-duplicate in case shared references ever happen (shouldn't), by id preserving first occurrence.
    seen = set()
    uniq = []
    for x in nodes_out:
        if x["id"] in seen:
            continue
        seen.add(x["id"])
        uniq.append(x)

    return {
        "regex": tree.regex,
        "normalized": tree.normalized,
        "alphabet": sorted(list(tree.alphabet)),
        "root_id": get_id(tree.root),
        "nodes": uniq,
    }
