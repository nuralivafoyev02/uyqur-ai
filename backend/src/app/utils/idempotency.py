from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IdempotencyClaim:
    update_id: int
    accepted: bool
    reason: str | None = None
