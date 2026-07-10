"""Parse financial amounts from news article text."""

import re

_CRORE_PATTERN = re.compile(
    r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(crore|cr|crores|lakh|lakhs|lac|million|mn|billion|bn)",
    re.IGNORECASE,
)
_BARE_CRORE_PATTERN = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*(crore|cr|crores|lakh|lakhs|lac|million|mn|billion|bn)",
    re.IGNORECASE,
)


class FinancialAmountParser:
    """Extracts deal/investment values in crore INR from text."""

    def parse_max_value_crore(self, text: str) -> float | None:
        """Return the largest plausible value in crore from combined title+body text."""
        if not text.strip():
            return None
        values: list[float] = []
        for pattern in (_CRORE_PATTERN, _BARE_CRORE_PATTERN):
            for match in pattern.finditer(text):
                amount = self._to_crore(match.group(1), match.group(2))
                if amount is not None and amount > 0:
                    values.append(amount)
        if not values:
            return None
        return max(values)

    @staticmethod
    def _to_crore(amount_str: str, unit: str) -> float | None:
        try:
            amount = float(amount_str.replace(",", ""))
        except ValueError:
            return None
        unit_lower = unit.lower()
        if unit_lower in {"crore", "cr", "crores"}:
            return amount
        if unit_lower in {"lakh", "lakhs", "lac"}:
            return amount / 100.0
        if unit_lower in {"million", "mn"}:
            return amount * 0.1
        if unit_lower in {"billion", "bn"}:
            return amount * 100.0
        return None
