"""
Regex normalization utilities.

Responsibilities:
- remove whitespace
- apply operator aliases (e.g., '+' -> '|')
- expand '?' (optional) into (A|&) so the parser/DFA builder does not need a dedicated operator
- insert explicit concatenation operator '.'
- append end-marker '#'
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Tuple


@dataclass(frozen=True)
class NormalizedRegex:
    """Result of normalization: a normalized expression string and the input alphabet."""
    expression: str
    alphabet: FrozenSet[str]


OPERATORS = {"|", ".", "*", "?", "(", ")"}
EPSILON = "&"
ENDMARK = "#"


def normalize(raw: str) -> NormalizedRegex:
    """
    Normalize a regex string into an explicit concatenation form.

    Supported surface syntax:
      - union:         |
      - concatenation: implicit (inserted as '.')
      - star:          *
      - optional:      ?  (expanded to (A|&) during normalization)
      - parentheses:   ( )
      - epsilon:       &

    Notes:
      - '#' is reserved as end-marker; if present in input, this raises.
      - The returned expression always has a final concatenation with '#'.
    """
    s = _strip_ws(raw)

    if ENDMARK in s:
        raise ValueError("Character '#' is reserved as end-marker and cannot appear in the regex.")

    # Expand optional operator first, so concatenation insertion sees explicit structure.
    s = _expand_optional(s)

    # Insert explicit concatenation '.'.
    s = _insert_concatenation(s)

    # Append end-marker as an explicit concatenation.
    if not s:
        # Empty regex is not meaningful; user should use '&' for epsilon.
        raise ValueError("Empty regex. Use '&' to denote epsilon.")
    s = f"({s}).{ENDMARK}"

    alphabet = frozenset(_collect_alphabet(s))
    # Alphabet must not include epsilon or end-marker.
    alphabet = frozenset(ch for ch in alphabet if ch not in {EPSILON, ENDMARK})

    return NormalizedRegex(expression=s, alphabet=alphabet)


def _strip_ws(s: str) -> str:
    return "".join(ch for ch in s if not ch.isspace())


def _collect_alphabet(expr: str) -> set[str]:
    out: set[str] = set()
    for ch in expr:
        if ch in OPERATORS or ch in {EPSILON, ENDMARK}:
            continue
        out.add(ch)
    return out


def _is_atom_start(ch: str) -> bool:
    """True if ch can start an atom."""
    return ch not in {"|", ".", "*", ")", ""}


def _is_atom_end(ch: str) -> bool:
    """True if ch can end an atom."""
    return ch not in {"|", ".", "(", ""}


def _insert_concatenation(s: str) -> str:
    """
    Insert '.' between tokens where concatenation is implied.

    Concatenation is implied between:
      - atom/end and atom/start
      - ')' and '('
      - '*' and atom/start
      - '*' and '('
      - atom/end and '('
      - ')' and atom/start
    """
    if not s:
        return s

    out: list[str] = []
    prev = ""
    for ch in s:
        if prev:
            if _needs_concat(prev, ch):
                out.append(".")
        out.append(ch)
        prev = ch
    return "".join(out)


def _needs_concat(a: str, b: str) -> bool:
    # a can be: literal, ')', '*', '&'
    # b can be: literal, '(', '&'
    a_is_end = (a not in {"|", ".", "(", ""}) and (a != "|")
    b_is_start = (b not in {"|", ".", ")", "*", ""}) and (b != "|")
    if not a_is_end or not b_is_start:
        return False
    # Disallow concat when b is ')' or '*' (can't start)
    if b in {")", "*"}:
        return False
    # Disallow concat when a is '(' or '|' or '.'
    if a in {"(", "|", "."}:
        return False
    return True


def _expand_optional(s: str) -> str:
    """
    Expand postfix '?' operator into an explicit union with epsilon.

    Examples:
      a?      -> (a|&)
      (ab)?   -> ((ab)|&)
      a*?     -> ((a*)|&)  (postfix binds to the immediately preceding atom)

    Algorithm:
      - scan left-to-right
      - whenever '?' is found, replace "atom?" with "(atom|&)" where atom is the previous atom
        (either a single literal/& or a parenthesized group or a starred atom).
    """
    if "?" not in s:
        return s

    out = list(s)
    i = 0
    # We'll rebuild using a stack of "segments" to simplify extraction of the previous atom.
    rebuilt: list[str] = []
    while i < len(out):
        ch = out[i]
        if ch != "?":
            rebuilt.append(ch)
            i += 1
            continue

        if not rebuilt:
            raise ValueError("Optional operator '?' cannot appear at the beginning.")
        atom = _pop_previous_atom(rebuilt)
        rebuilt.append("(")
        rebuilt.extend(atom)
        rebuilt.append("|")
        rebuilt.append(EPSILON)
        rebuilt.append(")")
        i += 1

    return "".join(rebuilt)


def _pop_previous_atom(buf: list[str]) -> list[str]:
    """
    Pop the previous atom from buf and return it as a list of chars.

    Atom forms (after whitespace stripping):
      - literal char (not an operator)
      - '&'
      - parenthesized group: (...)  (balanced)
      - atom with trailing '*' : atom*
    """
    # If the atom ends with '*', include it by first removing '*', then popping the underlying atom.
    if buf and buf[-1] == "*":
        buf.pop()
        inner = _pop_previous_atom(buf)
        return inner + ["*"]

    # Parenthesized group
    if buf and buf[-1] == ")":
        group: list[str] = []
        depth = 0
        while buf:
            c = buf.pop()
            group.append(c)
            if c == ")":
                depth += 1
            elif c == "(":
                depth -= 1
                if depth == 0:
                    break
        else:
            raise ValueError("Unbalanced parentheses near optional operator '?'.")
        group.reverse()
        return group

    # Single character atom (literal or '&')
    c = buf.pop()
    if c in {"|", ".", "(", ")"}:
        raise ValueError("Optional operator '?' must follow an atom.")
    return [c]
