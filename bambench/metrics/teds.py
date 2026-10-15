"""TEDS: tree-edit-distance similarity for tables (Zhong et al., 2020).

Tables are parsed to table > tr > td trees. th is treated as td and thead/tbody are
flattened so a pipe table and an HTML table with the same grid compare equal. Renaming a
cell costs its normalised content edit distance, or 1 if its span differs. TEDS-S ignores
cell content and scores structure only.
"""
from __future__ import annotations

from html.parser import HTMLParser

from .text import ned, normalize_text


class Node:
    __slots__ = ("tag", "span", "text", "children")

    def __init__(self, tag, span=(1, 1)):
        self.tag = tag
        self.span = span
        self.text = ""
        self.children: list[Node] = []


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("table")
        self.row: Node | None = None
        self.cell: Node | None = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self.depth += 1
        if self.depth > 1:
            return  # nested tables are folded into the cell text
        if tag == "tr":
            self.row = Node("tr")
            self.root.children.append(self.row)
        elif tag in ("td", "th"):
            if self.row is None:
                self.row = Node("tr")
                self.root.children.append(self.row)
            a = dict(attrs)

            def num(k):
                try:
                    return max(1, int(a.get(k) or 1))
                except ValueError:
                    return 1

            self.cell = Node("td", (num("colspan"), num("rowspan")))
            self.row.children.append(self.cell)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "table":
            self.depth -= 1
        elif tag in ("td", "th") and self.depth <= 1:
            self.cell = None
        elif tag == "tr" and self.depth <= 1:
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.text += data


def parse(html_table: str) -> Node:
    p = _Parser()
    p.feed(html_table)
    for row in p.root.children:
        for c in row.children:
            c.text = normalize_text(c.text)
    return p.root


def _postorder(root: Node):
    nodes, lmd = [], []

    def walk(n):
        leftmost = None
        for c in n.children:
            l = walk(c)
            if leftmost is None:
                leftmost = l
        nodes.append(n)
        if leftmost is None:
            leftmost = len(nodes) - 1
        lmd.append(leftmost)
        return leftmost

    walk(root)
    keyroots = sorted({l: i for i, l in enumerate(lmd)}.values())
    return nodes, lmd, keyroots


def tree_edit_distance(a: Node, b: Node, structure_only: bool = False) -> float:
    n1, l1, k1 = _postorder(a)
    n2, l2, k2 = _postorder(b)

    def rename(x: Node, y: Node) -> float:
        if x.tag != y.tag or x.span != y.span:
            return 1.0
        if x.tag == "td" and not structure_only:
            return ned(x.text, y.text)
        return 0.0

    td = [[0.0] * len(n2) for _ in n1]
    for i in k1:
        for j in k2:
            li, lj = l1[i], l2[j]
            m, n = i - li + 2, j - lj + 2
            fd = [[0.0] * n for _ in range(m)]
            for x in range(1, m):
                fd[x][0] = fd[x - 1][0] + 1
            for y in range(1, n):
                fd[0][y] = fd[0][y - 1] + 1
            for x in range(1, m):
                i1 = li + x - 1
                for y in range(1, n):
                    j1 = lj + y - 1
                    if l1[i1] == li and l2[j1] == lj:
                        v = min(fd[x - 1][y] + 1, fd[x][y - 1] + 1, fd[x - 1][y - 1] + rename(n1[i1], n2[j1]))
                        fd[x][y] = v
                        td[i1][j1] = v
                    else:
                        p, q = l1[i1] - li, l2[j1] - lj
                        fd[x][y] = min(fd[x - 1][y] + 1, fd[x][y - 1] + 1, fd[p][q] + td[i1][j1])
    return td[-1][-1]


def _size(n: Node) -> int:
    return 1 + sum(_size(c) for c in n.children)


def teds(gold_html: str, pred_html: str, structure_only: bool = False) -> float:
    g, p = parse(gold_html), parse(pred_html)
    denom = max(_size(g), _size(p))
    return 1.0 - tree_edit_distance(g, p, structure_only) / denom
