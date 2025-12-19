"""
Regex validation ("sanitization").

Supported surface syntax:
- union:         |
- concatenation: implicit
- Kleene star:   *
- optional:      ?  (postfix, expanded during normalization)
- parenthesis:   ( )
- epsilon:       &

Notes:
- '#' is reserved as end-marker and is not allowed in user input.
"""
from __future__ import annotations


OPERATORS = {"|", "*", "?", "(", ")"}
EPSILON = "&"
ENDMARK = "#"


def validate(regex: str) -> None:
    """
    Validate user-provided regex string.

    Raises ValueError with a readable message if invalid.
    """
    s = "".join(ch for ch in regex if not ch.isspace())

    if not s:
        raise ValueError("Empty regex. Use '&' to denote epsilon.")

    if ENDMARK in s:
        raise ValueError("Character '#' is reserved as end-marker and cannot appear in the regex.")

    _validate_chars(s)
    _validate_parentheses(s)
    _validate_operator_placement(s)


def _validate_chars(s: str) -> None:
    for ch in s:
        if ch == EPSILON:
            continue
        if ch in OPERATORS:
            continue
        # Allow any other single character as a literal (including digits, letters, etc.).
        # If you want to restrict this, do it here.
        if ch == ".":
            raise ValueError("'.' is reserved for internal concatenation; do not use it in input.")


def _validate_parentheses(s: str) -> None:
    depth = 0
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced parentheses: found ')' without matching '('.")
    if depth != 0:
        raise ValueError("Unbalanced parentheses: missing ')'.")


def _validate_operator_placement(s: str) -> None:
    """
    Basic operator placement rules for surface syntax.

    - '|' cannot be first or last, and cannot be adjacent to '|' or '(' on the right, or ')' on the left.
    - '*' and '?' are postfix and must follow an atom: literal, '&', or ')', or another postfix chain.
    - '(' cannot follow an atom without an operator; that's handled by normalization (implicit concat),
      but still allowed.
    """
    n = len(s)
    for i, ch in enumerate(s):
        prev = s[i - 1] if i > 0 else ""
        nxt = s[i + 1] if i + 1 < n else ""

        if ch == "|":
            if i == 0 or i == n - 1:
                raise ValueError("'|' cannot be at the beginning or end of the regex.")
            if prev in {"|", "("}:
                raise ValueError("Invalid placement of '|': cannot follow '|' or '('.")
            if nxt in {"|", ")", "*", "?"}:
                raise ValueError("Invalid placement of '|': cannot be followed by '|', ')', '*', or '?'.")
        elif ch in {"*", "?"}:
            if i == 0:
                raise ValueError(f"'{ch}' cannot be at the beginning of the regex.")
            if prev in {"|", "("}:
                raise ValueError(f"'{ch}' must follow an atom, not '{prev}'.")
        elif ch == ")":
            if prev in {"|", "("}:
                raise ValueError("Empty group '()' or invalid placement before ')'.")
        elif ch == "(":
            if nxt == ")":
                raise ValueError("Empty group '()' is not allowed.")
            if nxt in {"|", "*", "?"}:
                raise ValueError("Invalid placement: '(' cannot be followed by '|', '*', or '?'.")
