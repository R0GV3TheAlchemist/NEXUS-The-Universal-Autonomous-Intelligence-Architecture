"""Unit tests: Relationship graph engine — C03 §4."""

import pytest
from core.ontology.relationships import Relationship, RelationshipGraph, RelationshipType


@pytest.fixture
def graph():
    return RelationshipGraph()


class TestRelationshipGraph:
    def test_add_relationship_creates_edge(self, graph):
        rel = graph.add_relationship("A", "B", RelationshipType.INSTANTIATES)
        assert rel.source_id == "A"
        assert rel.target_id == "B"
        assert rel.type == RelationshipType.INSTANTIATES

    def test_weight_is_clamped(self, graph):
        rel = graph.add_relationship("A", "B", RelationshipType.ACTS_UPON, weight=5.0)
        assert rel.weight == 1.0
        rel2 = graph.add_relationship("A", "C", RelationshipType.ACTS_UPON, weight=-1.0)
        assert rel2.weight == 0.0

    def test_get_outgoing(self, graph):
        graph.add_relationship("A", "B", RelationshipType.INSTANTIATES)
        graph.add_relationship("A", "C", RelationshipType.ACTS_UPON)
        out = graph.get_outgoing("A")
        assert len(out) == 2

    def test_get_incoming(self, graph):
        graph.add_relationship("A", "B", RelationshipType.PARTNERS_WITH)
        graph.add_relationship("C", "B", RelationshipType.PARTNERS_WITH)
        incoming = graph.get_incoming("B")
        assert len(incoming) == 2

    def test_has_relationship(self, graph):
        graph.add_relationship("A", "B", RelationshipType.INSTANTIATES)
        assert graph.has_relationship("A", "B", RelationshipType.INSTANTIATES)
        assert not graph.has_relationship("A", "B", RelationshipType.ACTS_UPON)

    def test_remove_deactivates_relationship(self, graph):
        rel = graph.add_relationship("A", "B", RelationshipType.INSTANTIATES)
        graph.remove_relationship(rel.id)
        assert not graph.has_relationship("A", "B")

    def test_traverse_bfs(self, graph):
        graph.add_relationship("A", "B", RelationshipType.INSTANTIATES)
        graph.add_relationship("B", "C", RelationshipType.ACTS_UPON)
        graph.add_relationship("C", "D", RelationshipType.PARTNERS_WITH)
        visited = graph.traverse("A", max_depth=3)
        assert "A" in visited
        assert "B" in visited
        assert "C" in visited
        assert "D" in visited

    def test_traverse_respects_max_depth(self, graph):
        graph.add_relationship("A", "B", RelationshipType.INSTANTIATES)
        graph.add_relationship("B", "C", RelationshipType.ACTS_UPON)
        graph.add_relationship("C", "D", RelationshipType.PARTNERS_WITH)
        visited = graph.traverse("A", max_depth=1)
        assert "B" in visited
        assert "C" not in visited

    def test_get_neighbors_both_directions(self, graph):
        graph.add_relationship("A", "B", RelationshipType.INSTANTIATES)
        graph.add_relationship("C", "A", RelationshipType.IS_SERVED_BY)
        neighbors = graph.get_neighbors("A", direction="both")
        assert "B" in neighbors
        assert "C" in neighbors

    def test_entity_count(self, graph):
        graph.add_relationship("A", "B", RelationshipType.INSTANTIATES)
        graph.add_relationship("B", "C", RelationshipType.ACTS_UPON)
        assert graph.entity_count() == 3
