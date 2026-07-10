"""Formats V2 weighted score contributions for debug output."""

from morning_trading_agent.config.premarket_config import RankingWeightV2Config
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.entities.explanation import ScoreBreakdown


class WeightedContributionReportBuilder:
    """Builds per-dimension weighted contribution lines for a candidate."""

    def __init__(self, *, weight_config: RankingWeightV2Config | None = None) -> None:
        self._weights = weight_config or RankingWeightV2Config()

    def format_candidate(self, candidate: TradingCandidate) -> list[str]:
        """Return markdown lines for weighted contributions."""
        breakdown = candidate.score_breakdown
        quality = candidate.sentiment.catalyst_quality

        effective = candidate.effective_catalyst_score or candidate.catalyst_score
        magnitude = candidate.magnitude_score or (
            quality.magnitude_score if quality else 50.0
        )
        materiality = candidate.materiality_score or (
            quality.materiality_score if quality else 50.0
        )
        tradability = candidate.tradability_score or (
            quality.tradability_score if quality else 50.0
        )
        technical = candidate.technical_score
        sentiment = candidate.news_score
        confidence = candidate.confidence_score

        w = self._weights
        contributions = self._compute_contributions(
            effective_catalyst=effective,
            magnitude_score=magnitude,
            materiality_score=materiality,
            tradability_score=tradability,
            technical_score=technical,
            news_score=sentiment,
            confidence_score=confidence,
            breakdown=breakdown,
        )

        lines = [
            f"### {candidate.stock.symbol}",
            f"Catalyst: {candidate.sentiment.primary_catalyst_type.value} | "
            f"Magnitude: {quality.magnitude.value if quality else 'n/a'} ({magnitude:.0f})",
            f"Materiality: {materiality:.0f} | Tradability: {tradability:.0f} | "
            f"Technical: {technical:.0f} | Final: {candidate.final_score:.1f}",
            "",
            "Weighted contributions:",
        ]
        for label, score, weight_pct, contribution in contributions:
            lines.append(
                f"  {label}: {score:.0f} | Weight: {weight_pct:.0f}% | "
                f"Contribution: {contribution:.1f}"
            )
        lines.append(f"  Final Score: {candidate.final_score:.1f}")
        return lines

    def _compute_contributions(
        self,
        *,
        effective_catalyst: float,
        magnitude_score: float,
        materiality_score: float,
        tradability_score: float,
        technical_score: float,
        news_score: float,
        confidence_score: float,
        breakdown: ScoreBreakdown | None,
    ) -> list[tuple[str, float, float, float]]:
        w = self._weights
        dims = [
            ("Catalyst Score", effective_catalyst, w.catalyst * 100),
            ("Magnitude Score", magnitude_score, w.magnitude * 100),
            ("Materiality Score", materiality_score, w.materiality * 100),
            ("Tradability Score", tradability_score, w.tradability * 100),
            ("Technical Score", technical_score, w.technical * 100),
            ("Sentiment Score", news_score, w.sentiment * 100),
            ("Confidence Score", confidence_score, w.confidence * 100),
        ]

        recompute = (
            breakdown is not None
            and breakdown.final > 0
            and breakdown.weighted_catalyst == 0
        )
        result: list[tuple[str, float, float, float]] = []
        weight_map = {
            "Catalyst Score": (w.catalyst, breakdown.weighted_catalyst if breakdown and not recompute else None),
            "Magnitude Score": (w.magnitude, breakdown.weighted_magnitude if breakdown and not recompute else None),
            "Materiality Score": (w.materiality, breakdown.weighted_materiality if breakdown and not recompute else None),
            "Tradability Score": (w.tradability, breakdown.weighted_tradability if breakdown and not recompute else None),
            "Technical Score": (w.technical, breakdown.weighted_technical if breakdown and not recompute else None),
            "Sentiment Score": (w.sentiment, breakdown.weighted_sentiment if breakdown and not recompute else None),
            "Confidence Score": (w.confidence, breakdown.weighted_confidence if breakdown and not recompute else None),
        }
        for label, score, weight_pct in dims:
            weight_frac, weighted = weight_map[label]
            contribution = weighted if weighted is not None else score * weight_frac
            result.append((label, score, weight_pct, round(contribution, 1)))
        return result
