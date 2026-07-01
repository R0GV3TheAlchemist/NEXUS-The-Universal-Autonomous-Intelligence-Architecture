"""
GAIA MVP — World State
The persistent, versioned memory of what GAIA believes is real.
"Git for reality models." — every update is logged, every state is recoverable.
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

DEFAULT_PATH = Path("world_state.json")


class WorldState:

    def __init__(self):
        self.state: Dict[str, Any] = {}
        self._history: List[Dict] = []
        self._update_count: int = 0

    # ——— write ———

    def update(self, claim_result: Dict[str, Any]) -> None:
        """Receive an evaluated claim and update world state."""
        claim = claim_result["claim"]
        entry = {
            "id":           claim.id,
            "statement":    claim.statement,
            "sources":      claim.sources,
            "domain":       claim.domain,
            "confidence":   claim_result["confidence"],
            "status":       claim_result["status"],
            "contradiction_count": len(claim_result.get("contradictions", [])),
            "updated_at":   datetime.utcnow().isoformat(),
        }
        self.state[claim.id] = entry
        self._history.append({"update_index": self._update_count, **entry})
        self._update_count += 1

    # ——— query ———

    def query(self, keyword: str, min_confidence: float = 0.0) -> List[Dict]:
        """Return all entries whose statement contains a keyword."""
        kw = keyword.lower()
        results = [
            e for e in self.state.values()
            if kw in e["statement"].lower()
            and e["confidence"] >= min_confidence
        ]
        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    def disputed(self) -> List[Dict]:
        """Return all currently disputed entries."""
        return [e for e in self.state.values() if e["status"] == "disputed"]

    def snapshot(self) -> Dict[str, Any]:
        """Full world state snapshot."""
        return {
            "snapshot_at":   datetime.utcnow().isoformat(),
            "total_entries": len(self.state),
            "update_count":  self._update_count,
            "state":         dict(self.state)
        }

    def stats(self) -> Dict[str, Any]:
        status_counts: Dict[str, int] = {}
        for e in self.state.values():
            s = e["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        confs = [e["confidence"] for e in self.state.values()]
        return {
            "total":             len(self.state),
            "update_count":      self._update_count,
            "status_breakdown":  status_counts,
            "avg_confidence":    round(sum(confs)/len(confs), 4) if confs else 0.0,
            "disputed":          status_counts.get("disputed", 0),
        }

    # ——— persistence ———

    def save(self, path: Path = DEFAULT_PATH) -> None:
        """Persist world state to JSON. Every save is a versioned truth commit."""
        with open(path, "w") as f:
            json.dump(self.snapshot(), f, indent=2)

    def load(self, path: Path = DEFAULT_PATH) -> None:
        """Load world state from JSON."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
                self.state = data.get("state", {})
                self._update_count = data.get("update_count", 0)
                print(f"  World state loaded: {len(self.state)} entries, "
                      f"{self._update_count} prior updates.")
        except FileNotFoundError:
            self.state = {}
            print("  No prior world state found. Starting fresh.")
