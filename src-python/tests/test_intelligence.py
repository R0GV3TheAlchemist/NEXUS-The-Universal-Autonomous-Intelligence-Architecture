"""tests/test_intelligence.py

Test scaffold for src-python/intelligence

Covers: CognitiveKernel, Agent, Perception, KnowledgeGraph,
        Explainability from intelligence.*
"""
import pytest

intelligence = pytest.importorskip("intelligence")


class TestCognitiveKernel:
    """CognitiveKernel orchestrates all intelligence subsystems."""

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_kernel_initialises(self):
        from intelligence.cognitivekernel import CognitiveKernel
        kernel = CognitiveKernel()
        assert kernel is not None

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_kernel_perceive_does_not_raise(self):
        from intelligence.cognitivekernel import CognitiveKernel
        kernel = CognitiveKernel()
        kernel.perceive({"modality": "text", "data": "hello world"})


class TestKnowledgeGraph:
    """KnowledgeGraph manages episodic, semantic, and procedural memory."""

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_add_and_query_node(self):
        from intelligence.knowledgegraph import KnowledgeGraph
        kg = KnowledgeGraph()
        kg.add_node(node_id="n1", label="concept", properties={"name": "NEXUS"})
        results = kg.query("NEXUS")
        assert len(results) >= 1

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_episodic_memory_stores_event(self):
        from intelligence.knowledgegraph import KnowledgeGraph
        kg = KnowledgeGraph()
        kg.add_episode(content="Session started.", timestamp=None)
