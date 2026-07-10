"""Sector taxonomy for indirect beneficiary discovery."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SectorMapping(BaseModel):
    """Maps policy/commodity keywords to expected beneficiary symbols."""

    keywords: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    role: str = "SECTOR_PEER"
    weight: float = 0.35


class SectorTaxonomy(BaseModel):
    """Loaded sector taxonomy configuration."""

    mappings: list[SectorMapping] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path | None = None) -> SectorTaxonomy:
        root = Path(__file__).resolve().parents[4]
        file_path = path or (root / "config" / "sector_taxonomy.yaml")
        if not file_path.exists():
            return cls()
        raw = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        return cls.model_validate(raw)

    def match_symbols(self, text: str) -> list[tuple[str, str, float]]:
        """Return (symbol, role, weight) for keyword matches in text."""
        lower = text.lower()
        results: list[tuple[str, str, float]] = []
        seen: set[str] = set()
        for mapping in self.mappings:
            if not any(keyword.lower() in lower for keyword in mapping.keywords):
                continue
            for symbol in mapping.symbols:
                if symbol in seen:
                    continue
                seen.add(symbol)
                results.append((symbol, mapping.role, mapping.weight))
        return results
