"""Static NSE symbol to sector mappings for sector momentum scoring."""

from typing import Literal

SectorName = Literal[
    "IT",
    "Banking",
    "Power",
    "Railway",
    "Infrastructure",
    "Capital_Goods",
    "Pharma",
    "Auto",
    "Metals",
    "Other",
]

SYMBOL_SECTOR_MAP: dict[str, SectorName] = {
    "TCS": "IT",
    "INFY": "IT",
    "WIPRO": "IT",
    "HCLTECH": "IT",
    "TECHM": "IT",
    "HDFCBANK": "Banking",
    "ICICIBANK": "Banking",
    "KOTAKBANK": "Banking",
    "SBIN": "Banking",
    "AXISBANK": "Banking",
    "FEDERALBNK": "Banking",
    "NTPC": "Power",
    "POWERGRID": "Power",
    "TATAPOWER": "Power",
    "ADANIPOWER": "Power",
    "IRCTC": "Railway",
    "RVNL": "Railway",
    "IRFC": "Railway",
    "TEXRAIL": "Railway",
    "CONCOR": "Railway",
    "LT": "Infrastructure",
    "GTLINFRA": "Infrastructure",
    "ADANIPORTS": "Infrastructure",
    "GMRAIRPORT": "Infrastructure",
    "ABB": "Capital_Goods",
    "SIEMENS": "Capital_Goods",
    "BHEL": "Capital_Goods",
    "NH": "Capital_Goods",
    "JBMA": "Auto",
    "ATLANTAELE": "Auto",
    "SUNPHARMA": "Pharma",
    "DRREDDY": "Pharma",
    "TATASTEEL": "Metals",
    "HINDALCO": "Metals",
}


def sector_for_symbol(symbol: str) -> SectorName:
    """Return sector for symbol, defaulting to Other."""
    return SYMBOL_SECTOR_MAP.get(symbol.upper(), "Other")
