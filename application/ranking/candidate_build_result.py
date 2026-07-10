"""Result of building trading candidates from stocks."""

from dataclasses import dataclass, field

from morning_trading_agent.domain.entities.article import TradingCandidate


@dataclass
class CandidateBuildResult:
    """All built candidates plus symbols dropped during join."""

    candidates: list[TradingCandidate] = field(default_factory=list)
    dropped_missing_sentiment: list[str] = field(default_factory=list)
    dropped_missing_technical: list[str] = field(default_factory=list)
    dropped_tradability: list[str] = field(default_factory=list)
