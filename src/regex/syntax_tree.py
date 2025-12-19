"""
Syntax tree construction for the regex language and followpos computation.

This implementation uses a small recursive-descent parser over the normalized expression
(from `src.regex.format.normalize`) where concatenation is explicit via '.' and the
end-marker '#' is present.

It produces a syntax tree with nullable/firstpos/lastpos/followpos data (Aho-Sethi-Ullman)
used by the direct DFA construction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from src.regex.format import ENDMARK, EPSILON, NormalizedRegex, normalize
from src.regex.sanitization import validate


@dataclass
class Node:
    value: str
    left: Optional["Node"] = None
    right: Optional["Node"] = None

    # Position info for leaves (literals and end-marker); epsilon is not a position.
    serial_number: Optional[int] = None

    # Aho-Sethi-Ullman attributes
    nullable: bool = False
    first_pos: Set["Node"] = field(default_factory=set)
    last_pos: Set["Node"] = field(default_factory=set)
    follow_pos: Set["Node"] = field(default_factory=set)

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def calculate_follow_pos(self) -> None:
        """
        Compute nullable/first_pos/last_pos and populate follow_pos for all nodes.
        This is a post-order traversal.
        """
        if self.left:
            self.left.calculate_follow_pos()
        if self.right:
            self.right.calculate_follow_pos()

        if self.is_leaf():
            if self.value == EPSILON:
                self.nullable = True
                self.first_pos = set()
                self.last_pos = set()
            else:
                self.nullable = False
                self.first_pos = {self}
                self.last_pos = {self}
            return

        if self.value == "|":
            assert self.left and self.right
            self.nullable = self.left.nullable or self.right.nullable
            self.first_pos = set(self.left.first_pos) | set(self.right.first_pos)
            self.last_pos = set(self.left.last_pos) | set(self.right.last_pos)

        elif self.value == ".":
            assert self.left and self.right
            self.nullable = self.left.nullable and self.right.nullable
            self.first_pos = set(self.left.first_pos)
            if self.left.nullable:
                self.first_pos |= set(self.right.first_pos)
            self.last_pos = set(self.right.last_pos)
            if self.right.nullable:
                self.last_pos |= set(self.left.last_pos)

            # followpos: for every i in lastpos(left), add firstpos(right)
            for i in self.left.last_pos:
                i.follow_pos |= set(self.right.first_pos)

        elif self.value == "*":
            assert self.left and not self.right
            self.nullable = True
            self.first_pos = set(self.left.first_pos)
            self.last_pos = set(self.left.last_pos)

            # followpos: for every i in lastpos(child), add firstpos(child)
            for i in self.left.last_pos:
                i.follow_pos |= set(self.left.first_pos)

        else:
            raise ValueError(f"Unknown operator node value: {self.value!r}")

    def __hash__(self) -> int:
        if self.serial_number is None:
            # Internal nodes or epsilon leaves should never be hashed
            raise TypeError("Only leaf nodes with serial_number can be hashed")
        return hash(self.serial_number)


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self.serial_number == other.serial_number



class _Parser:
    """
    Recursive-descent parser for the normalized regex syntax:

      expr   := union
      union  := concat ('|' concat)*
      concat := repeat ('.' repeat)*
      repeat := atom ('*')*
      atom   := literal | '&' | '#' | '(' expr ')'

    Optional '?' is not parsed here: it is expanded during normalization.
    """

    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def parse(self) -> Node:
        node = self._parse_union()
        if self._peek():
            raise ValueError(f"Unexpected trailing input at pos {self.i}: {self.s[self.i:]!r}")
        return node

    def _peek(self) -> str:
        return self.s[self.i] if self.i < len(self.s) else ""

    def _eat(self, ch: str) -> None:
        if self._peek() != ch:
            raise ValueError(f"Expected {ch!r} at pos {self.i}, got {self._peek()!r}")
        self.i += 1

    def _parse_union(self) -> Node:
        node = self._parse_concat()
        while self._peek() == "|":
            self._eat("|")
            right = self._parse_concat()
            node = Node("|", left=node, right=right)
        return node

    def _parse_concat(self) -> Node:
        node = self._parse_repeat()
        while self._peek() == ".":
            self._eat(".")
            right = self._parse_repeat()
            node = Node(".", left=node, right=right)
        return node

    def _parse_repeat(self) -> Node:
        node = self._parse_atom()
        while self._peek() == "*":
            self._eat("*")
            node = Node("*", left=node)
        return node

    def _parse_atom(self) -> Node:
        ch = self._peek()
        if not ch:
            raise ValueError(f"Unexpected end of input at pos {self.i}.")

        if ch == "(":
            self._eat("(")
            node = self._parse_union()
            self._eat(")")
            return node

        if ch in {"|", ".", ")", "*"}:
            raise ValueError(f"Unexpected token {ch!r} at pos {self.i}.")

        # literal leaf, epsilon, or end-marker
        self.i += 1
        return Node(ch)


class SyntaxTree:
    """
    Public wrapper: validates, normalizes, parses, and assigns leaf positions.
    """

    def __init__(self, regex: str):
        validate(regex)
        normalized: NormalizedRegex = normalize(regex)
        self.regex = regex
        self.normalized = normalized.expression
        self.alphabet = normalized.alphabet

        parser = _Parser(self.normalized)
        self.root: Node = parser.parse()

        # Assign positions to all leaves excluding epsilon.
        self.nodes: List[Node] = []
        self._assign_positions(self.root)

    def _assign_positions(self, node: Node) -> None:
        if node.left:
            self._assign_positions(node.left)
        if node.right:
            self._assign_positions(node.right)

        if node.is_leaf():
            if node.value == EPSILON:
                node.serial_number = None
            else:
                node.serial_number = len(self.nodes) + 1
                self.nodes.append(node)

    def end_marker_position(self) -> int:
        """
        Return the serial_number of the end-marker '#' leaf.
        """
        for n in self.nodes:
            if n.value == ENDMARK:
                assert n.serial_number is not None
                return n.serial_number
        raise ValueError("Normalized regex is missing end-marker '#'.")
