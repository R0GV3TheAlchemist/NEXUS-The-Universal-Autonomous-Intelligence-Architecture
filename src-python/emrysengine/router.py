"""emrysengine.router

EmrysEngine initialisation helper.

Follows the engine/router pattern used across NEXUS modules.
Called during application startup to wire EmrysEngine into
the NEXUS orchestration layer.
"""
from __future__ import annotations

import logging
from emrysengine.engine import EmrysConfig, EmrysEngine

logger = logging.getLogger("emrysengine.router")


def init_emrys_engine(config: EmrysConfig | None = None) -> EmrysEngine:
    """Initialise and return an EmrysEngine instance.

    Args:
        config: Optional EmrysConfig. Defaults to EmrysConfig() if None.

    Returns:
        Configured EmrysEngine instance.
    """
    engine = EmrysEngine(config=config)
    logger.info("EmrysEngine initialised via router.")
    return engine
