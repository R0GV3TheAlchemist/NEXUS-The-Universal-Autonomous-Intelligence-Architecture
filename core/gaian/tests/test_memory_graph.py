"""
Tests for MemoryGraph — GAIAN holographic memory.
"""

from core.gaian.memory_graph import MemoryGraph


def test_remember_and_recall():
    mg = MemoryGraph(gaian_id="g-001")
    node = mg.remember("First conversation with human", salience=0.8)
    recalled = mg.recall(node.node_id)
    assert recalled is not None
    assert recalled.content == "First conversation with human"
    assert recalled.access_count == 1


def test_forget_removes_node_and_edges():
    mg = MemoryGraph(gaian_id="g-001")
    a = mg.remember("Node A")
    b = mg.remember("Node B")
    mg.connect(a.node_id, b.node_id)
    assert len(mg._edges) == 1
    mg.forget(a.node_id)
    assert a.node_id not in mg._nodes
    assert len(mg._edges) == 0


def test_search_by_tag():
    mg = MemoryGraph(gaian_id="g-001")
    mg.remember("Important moment", tags=["milestone", "emotion"])
    mg.remember("Another moment", tags=["emotion"])
    results = mg.search_by_tag("milestone")
    assert len(results) == 1


def test_decay_reduces_salience():
    mg = MemoryGraph(gaian_id="g-001")
    node = mg.remember("Old memory", salience=0.5)
    mg.apply_decay(rate=0.1)
    assert node.salience < 0.5


def test_prune_removes_low_salience():
    mg = MemoryGraph(gaian_id="g-001")
    mg.remember("Vivid", salience=0.9)
    mg.remember("Fading", salience=0.02)
    removed = mg.prune_forgotten(threshold=0.05)
    assert removed == 1
    assert len(mg._nodes) == 1


def test_most_salient_ordering():
    mg = MemoryGraph(gaian_id="g-001")
    mg.remember("Low", salience=0.1)
    mg.remember("High", salience=0.9)
    mg.remember("Mid", salience=0.5)
    top = mg.most_salient(top_n=2)
    assert top[0].salience == 0.9
