"""Load catalyst taxonomy seed data from JSON."""

from __future__ import annotations

import json
from pathlib import Path

from morning_trading_agent.domain.entities.catalyst_taxonomy import (
    CatalystTaxonomyEntry,
    CatalystTaxonomySeedData,
)


def default_seed_path() -> Path:
    """Resolve default seed JSON path."""
    root = Path(__file__).resolve().parents[5]
    return root / "config" / "catalyst_taxonomy_seed.json"


def load_catalyst_taxonomy_seed(path: Path | None = None) -> CatalystTaxonomySeedData:
    """Load seed entries and aliases from JSON."""
    file_path = path or default_seed_path()
    if not file_path.exists():
        return CatalystTaxonomySeedData()
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    entries = [CatalystTaxonomyEntry.model_validate(item) for item in raw.get("entries", [])]
    aliases = {str(k): str(v) for k, v in (raw.get("aliases") or {}).items()}
    return CatalystTaxonomySeedData(entries=entries, aliases=aliases)
