"""Tests for the Dijkstra graph service."""

import pytest
from src.application.services.graph_service import shortestPath


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_line_graph():
    """A → B → C with weights 1 and 2."""
    return [
        ("A", "B", 1),
        ("B", "C", 2),
    ]


def _make_forked_graph():
    """
    A → B (w=1), A → C (w=5), B → C (w=1)
    Shortest A→C should be A→B→C (cost=2), not A→C (cost=5).
    """
    return [
        ("A", "B", 1),
        ("A", "C", 5),
        ("B", "C", 1),
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestShortestPath:
    """Unit tests for shortestPath (Dijkstra)."""

    def test_direct_path(self):
        edges = _make_line_graph()
        cost, path = shortestPath(edges, "A", "B")
        assert cost == 1
        assert path == ["A", "B"]

    def test_two_hops(self):
        edges = _make_line_graph()
        cost, path = shortestPath(edges, "A", "C")
        assert cost == 3
        assert path == ["A", "B", "C"]

    def test_chooses_cheaper_route(self):
        edges = _make_forked_graph()
        cost, path = shortestPath(edges, "A", "C")
        assert cost == 2
        assert path == ["A", "B", "C"]

    def test_same_source_and_sink(self):
        edges = _make_line_graph()
        cost, path = shortestPath(edges, "A", "A")
        assert cost == 0
        assert path == ["A"]

    def test_unreachable_returns_fallback(self):
        """Unreachable sink returns (0, [source]) as per legacy contract."""
        edges = [("A", "B", 1)]
        cost, path = shortestPath(edges, "A", "Z")
        assert cost == 0
        assert path == ["A"]

    def test_empty_graph(self):
        cost, path = shortestPath([], "A", "A")
        assert cost == 0
        assert path == ["A"]

    def test_tuple_node_keys(self):
        """Grid coordinates are tuples — ensure hashability."""
        edges = [
            ((0, 0), (0, 1), 1),
            ((0, 1), (0, 2), 1),
        ]
        cost, path = shortestPath(edges, (0, 0), (0, 2))
        assert cost == 2
        assert path == [(0, 0), (0, 1), (0, 2)]
