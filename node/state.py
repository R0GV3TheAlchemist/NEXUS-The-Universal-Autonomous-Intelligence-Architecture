"""
GAIA Node State — v0.6 (Trust-Aware)
Local world model with injected TrustProfile.
Every merge now updates trust based on adversarial validation results.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class NodeState:

    def __init__(
        self,
        node_id: str = "local",
        domain: Optional[str] = None,
        trust: float = 1.0
    ):
        self.node_id      = node_id
        self.domain       = domain
        self.trust        = trust
        self.trust_profile = None   # injected at runtime via set_trust()
        self._data: Dict[str, Any] = {}
        self._merge_log: List[Dict] = []
        self._update_count = 0
        self._state_file = Path(f"world_state_{node_id}.json")
        self._load()

    def set_trust(self, trust_profile) -> None:
        """Inject a TrustProfile at runtime."""
        self.trust_profile = trust_profile
        self.trust = trust_profile.score

    # --- Write ---

    def update(self, key: str, value: Dict[str, Any]) -> None:
        self._data[key] = {
            **value,
            "node_id":    self.node_id,
            "updated_at": datetime.utcnow().isoformat()
        }
        self._update_count += 1

    def merge(self, incoming: Dict[str, Any]) -> Dict[str, Any]:
        peer_id    = incoming.get("node_id", "unknown")
        peer_state = incoming.get("state", {})
        accepted = 0
        rejected = 0
        conflicts = []

        for k, v in peer_state.items():
            if not isinstance(v, dict):
                continue
            incoming_conf = v.get("confidence", 0)
            existing_conf = self._data.get(k, {}).get("confidence", -1)

            if k not in self._data:
                self._data[k] = {**v, "merged_from": peer_id}
                accepted += 1
            elif incoming_conf > existing_conf:
                old_status = self._data[k].get("status")
                new_status = v.get("status")
                if old_status != new_status:
                    conflicts.append({
                        "claim_id":         k,
                        "old_status":        old_status,
                        "new_status":        new_status,
                        "confidence_delta":  round(incoming_conf - existing_conf, 4)
                    })
                self._data[k] = {**v, "merged_from": peer_id}
                accepted += 1
            else:
                rejected += 1

        self._merge_log.append({
            "peer":      peer_id,
            "timestamp": datetime.utcnow().isoformat(),
            "accepted":  accepted,
            "rejected":  rejected,
            "conflicts": conflicts
        })
        self.save()
        return {
            "status":    "merged",
            "node_id":   self.node_id,
            "peer":      peer_id,
            "accepted":  accepted,
            "rejected":  rejected,
            "conflicts": len(conflicts)
        }

    # --- Read ---

    def get(self) -> Dict[str, Any]:
        return dict(self._data)

    def get_snapshot(self) -> Dict[str, Any]:
        trust_summary = (
            self.trust_profile.summary()
            if self.trust_profile else {"score": self.trust}
        )
        return {
            "node_id":      self.node_id,
            "domain":       self.domain,
            "trust":        self.trust_profile.score if self.trust_profile else self.trust,
            "trust_profile": trust_summary,
            "claim_count":  len(self._data),
            "update_count": self._update_count,
            "snapshot_at":  datetime.utcnow().isoformat(),
            "state":        dict(self._data)
        }

    def stats(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        confs = []
        for v in self._data.values():
            if isinstance(v, dict):
                s = v.get("status", "unknown")
                statuses[s] = statuses.get(s, 0) + 1
                confs.append(v.get("confidence", 0))
        base = {
            "node_id":          self.node_id,
            "domain":           self.domain,
            "trust":            self.trust_profile.score if self.trust_profile else self.trust,
            "total_claims":     len(self._data),
            "update_count":     self._update_count,
            "merge_count":      len(self._merge_log),
            "avg_confidence":   round(sum(confs)/len(confs), 4) if confs else 0.0,
            "status_breakdown": statuses
        }
        if self.trust_profile:
            base["trust_profile"] = self.trust_profile.summary()
        return base

    # --- Persistence ---

    def save(self) -> None:
        payload = {
            "node_id":      self.node_id,
            "saved_at":     datetime.utcnow().isoformat(),
            "gaia_version": "0.6.0",
            "state":        self._data
        }
        with open(self._state_file, "w") as f:
            json.dump(payload, f, indent=2, default=str)

    def _load(self) -> None:
        try:
            with open(self._state_file, "r") as f:
                data = json.load(f)
            self._data = data.get("state", {})
            print(f"  Loaded prior state [{self.node_id}]: {len(self._data)} claims")
        except FileNotFoundError:
            pass
