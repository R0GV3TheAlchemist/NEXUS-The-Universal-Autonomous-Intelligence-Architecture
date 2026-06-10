"""
core/knowledge_matrix.py — STUB (Phase C)

Physical implementation has moved to core/memory/knowledge_matrix.py.
This stub re-exports the full public surface so all existing callers
continue to work without any changes.
"""
from core.memory.knowledge_matrix import *       # noqa: F403
from core.memory.knowledge_matrix import (
    EpistemicTier,
    KnowledgeDomain,
    KnowledgeMatrixEngine,
    KNOWLEDGE_MATRIX,
    get_knowledge_engine,
)
