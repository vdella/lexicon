from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Set, Tuple

import plotly.graph_objects as go

from src.regex.syntax_tree import SyntaxTree, Node
from src.regex.conversion import fa_from
from src.automata.structures import FiniteAutomata

try:
    import graphviz  # type: ignore
except Exception:  # pragma: no cover
    graphviz = None


# ----------------------------
# Tree utilities (Dash parity)
# ----------------------------

def _preorder_nodes(root: Node) -> List[Node]:
    nodes: List[Node] = []

    def visit(n: Optional[Node]) -> None:
        if not n:
            return
        nodes.append(n)
        visit(n.left)
        visit(n.right)

    visit(root)
    return nodes


def _reverse_level_order_ids(root: Node) -> Dict[int, int]:
    # Reproduce DashTree.nodes_by_reverse_level_order_traversal logic:
    # queue: push right then left; stack; then pop to assign serial starting 1
    queue: List[Node] = [root]
    stack: List[Node] = []
    while queue:
        current = queue.pop(0)
        stack.append(current)
        if current.right:
            queue.append(current.right)
        if current.left:
            queue.append(current.left)

    serial = 1
    mapping: Dict[int, int] = {}
    while stack:
        current = stack.pop()
        mapping[id(current)] = serial
        serial += 1
    return mapping


def _pos_set_str(pos: Set[Node]) -> str:
    ids = [n.serial_number for n in pos if n.serial_number is not None]
    ids_sorted = sorted(ids)
    return "{" + ", ".join(str(i) for i in ids_sorted) + "}"


def _node_metadata_html(n: Node) -> str:
    # Mirrors the DashNode.__str__ display
    return (
        f"nullable: {bool(n.nullable)}<br />"
        f"first_pos: {_pos_set_str(n.first_pos)}<br />"
        f"last_pos: {_pos_set_str(n.last_pos)}<br />"
    )


# ----------------------------
# Figure building (no igraph)
# ----------------------------

def _layout_binary_tree(root: Node) -> Dict[int, Tuple[float, float]]:
    # Simple deterministic layout:
    # - x = inorder index for leaves; internal nodes x = midpoint(children)
    # - y = depth
    x_counter = 0
    coords: Dict[int, Tuple[float, float]] = {}

    def inorder(n: Optional[Node], depth: int) -> float:
        nonlocal x_counter
        if not n:
            return 0.0

        if n.left is None and n.right is None:
            x = float(x_counter)
            x_counter += 1
        else:
            left_x = inorder(n.left, depth + 1) if n.left else float(x_counter)
            right_x = inorder(n.right, depth + 1) if n.right else float(x_counter)
            x = (left_x + right_x) / 2.0

        coords[id(n)] = (x, float(depth))
        return x

    inorder(root, 0)

    xs = [x for (x, _y) in coords.values()]
    if xs:
        min_x, max_x = min(xs), max(xs)
        span = max(max_x - min_x, 1.0)
        for k, (x, y) in list(coords.items()):
            nx = (x - min_x) / span
            coords[k] = (nx, y)

    return coords


def build_plotly_figure(tree: SyntaxTree, active_page: int) -> Dict[str, Any]:
    root = tree.root
    coords = _layout_binary_tree(root)

    preorder = _preorder_nodes(root)
    reverse_ids = _reverse_level_order_ids(root)

    # Dash semantics:
    # - "no active_page" => no hoverinfo
    # - active_page >= 1 reveals nodes where reverse_id <= active_page
    if active_page > 0:
        visible = {id(n): (reverse_ids[id(n)] <= active_page) for n in preorder}
    else:
        visible = {id(n): False for n in preorder}

    # Edge traces
    Xe: List[float] = []
    Ye: List[float] = []

    def add_edge(a: Node, b: Node) -> None:
        xa, ya = coords[id(a)]
        xb, yb = coords[id(b)]
        Xe.extend([xa, xb, None])
        Ye.extend([-ya, -yb, None])

    for n in preorder:
        if n.left:
            add_edge(n, n.left)
        if n.right:
            add_edge(n, n.right)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=Xe, y=Ye,
        mode="lines",
        hoverinfo="none",
        line=dict(width=1),
    ))

    # Node trace
    Xn = [coords[id(n)][0] for n in preorder]
    Yn = [-coords[id(n)][1] for n in preorder]

    labels = [f"{reverse_ids[id(n)]}: {n.value}" for n in preorder]
    customdata = [_node_metadata_html(n) if visible[id(n)] else "" for n in preorder]
    opacities = [1.0 if visible[id(n)] else 0.4 for n in preorder]
    text_colors = ["rgb(255, 255, 255)" if visible[id(n)] else "rgb(119, 52, 235)" for n in preorder]

    fig.add_trace(go.Scatter(
        x=Xn, y=Yn,
        mode="markers+text",
        text=labels,
        customdata=customdata,
        hovertemplate="%{customdata}<extra></extra>" if active_page > 0 else None,
        marker=dict(size=26, opacity=opacities),
        textfont=dict(color=text_colors),
        opacity=1.0,
    ))

    fig.update_layout(
        title_text="Lexical analysis tree",
        title_x=0.5,
        font_size=12,
        showlegend=False,
        xaxis_visible=False,
        yaxis_visible=False,
        margin=dict(l=40, r=40, b=85, t=100),
        hovermode="closest" if active_page > 0 else False,
    )

    return fig.to_dict()


def page_quantity(tree: SyntaxTree) -> int:
    return len(_preorder_nodes(tree.root)) + 1


# ----------------------------
# follow_pos table (Dash parity)
# ----------------------------

def follow_pos_table(tree: SyntaxTree) -> List[Dict[str, Any]]:
    tree.root.calculate_follow_pos()

    q: List[Node] = [tree.root]
    operators = {".", "*", "|"}

    def skin(nodes: Set[Node]) -> str:
        ids = sorted([n.serial_number for n in nodes if n.serial_number is not None])
        return "".join(str(i) for i in ids)

    out: Dict[int, str] = {}

    while q:
        cur = q.pop(0)

        if cur.left:
            q.append(cur.left)
        if cur.right:
            q.append(cur.right)

        # Only terminals with positions
        if cur.value in operators:
            continue
        if cur.serial_number is None:
            continue

        out[int(cur.serial_number)] = skin(set(cur.follow_pos))

    return [{"Node n": k, "follow_pos(n)": v} for k, v in sorted(out.items())]


# ----------------------------
# FA table + diagram
# ----------------------------

def fa_table_from_regex(regex: str) -> List[Dict[str, str]]:
    fa = fa_from(regex)
    rows: List[Dict[str, str]] = []
    for (src, sym), dsts in fa.transitions.items():
        for dst in sorted(dsts, key=lambda s: s.label):
            rows.append({
                "(source_state, symbol)": f"({src.label}, {sym})",
                "destiny_state": dst.label,
            })
    return rows


def fa_diagram(fa: FiniteAutomata) -> Tuple[str, Optional[str]]:
    # Returns (dot_source, png_data_url or None)
    dot_lines: List[str] = []
    dot_lines.append("digraph finite_automata {")
    dot_lines.append("  rankdir=LR;")
    dot_lines.append("  node [shape=circle];")

    initial = fa.initial_state.label if fa.initial_state else None
    finals = {s.label for s in fa.final_states}

    for s in sorted(fa.states, key=lambda st: st.label):
        if s.label in finals:
            dot_lines.append(f'  "{s.label}" [shape=doublecircle];')
        else:
            dot_lines.append(f'  "{s.label}";')

    if initial is not None:
        dot_lines.append('  "__start" [style=invis];')
        dot_lines.append(f'  "__start" -> "{initial}";')

    for (src, sym), dsts in fa.transitions.items():
        for dst in dsts:
            dot_lines.append(f'  "{src.label}" -> "{dst.label}" [label="{sym}"];')

    dot_lines.append("}")
    dot_source = "\n".join(dot_lines)

    png_data_url: Optional[str] = None
    if graphviz is not None:
        try:
            g = graphviz.Source(dot_source)
            png_bytes = g.pipe(format="png")
            png_data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8")
        except Exception:
            png_data_url = None

    return dot_source, png_data_url


def analyze(regex: str, active_page: int = 0) -> Dict[str, Any]:
    tree = SyntaxTree(regex)
    tree.root.calculate_follow_pos()

    fig = build_plotly_figure(tree, active_page=active_page)
    fp = follow_pos_table(tree)

    fa = fa_from(regex)
    fa_rows = fa_table_from_regex(regex)

    dot_source, png = fa_diagram(fa)

    return {
        "regex": regex,
        "page_quantity": page_quantity(tree),
        "figure": fig,
        "follow_pos_table": fp,
        "fa_table": fa_rows,
        "fa_dot": dot_source,
        "fa_png": png,
    }
