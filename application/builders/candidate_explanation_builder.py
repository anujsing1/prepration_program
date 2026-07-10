"""Builds human-readable explanations for ranked candidates."""

from morning_trading_agent.config.premarket_config import RankingWeightV2Config
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.entities.explanation import CandidateExplanation, ScoreBreakdown
from morning_trading_agent.domain.value_objects.catalyst import WEAK_CATALYST_TYPES, CatalystType
from morning_trading_agent.domain.value_objects.catalyst_quality import CatalystMagnitude
from morning_trading_agent.domain.value_objects.sentiment import SentimentDirection


class CandidateExplanationBuilder:
    """Generates explainability metadata for ranked watchlist candidates."""

    def build(self, candidate: TradingCandidate) -> CandidateExplanation:
        """Build a complete explanation for one candidate."""
        quality = candidate.sentiment.catalyst_quality
        primary_catalyst = candidate.sentiment.primary_catalyst_summary or candidate.sentiment.reason
        technical_summary = self._technical_summary(candidate)
        risk_factors = self._risk_factors(candidate)
        confidence_summary = (
            f"Confidence {candidate.confidence_score:.0f}/100 "
            f"({candidate.sentiment.direction.value})"
        )
        reason_for_ranking = self._reason_for_ranking(candidate)
        magnitude_label = quality.magnitude.value if quality else ""
        materiality = candidate.materiality_score or (quality.materiality_score if quality else None)
        tradability = candidate.tradability_score or (quality.tradability_score if quality else None)

        return CandidateExplanation(
            primary_catalyst=primary_catalyst,
            technical_summary=technical_summary,
            risk_factors=risk_factors,
            freshness_summary=f"{candidate.freshness_score:.0f}/100",
            confidence_summary=confidence_summary,
            reason_for_ranking=reason_for_ranking,
            catalyst_magnitude=magnitude_label,
            materiality_score=materiality,
            tradability_score=tradability,
        )

    def enrich(self, candidate: TradingCandidate) -> TradingCandidate:
        """Attach explanation to a candidate."""
        explanation = self.build(candidate)
        return candidate.model_copy(update={"explanation": explanation})

    def ranking_explanation_dict(self, candidate: TradingCandidate) -> dict[str, float | str | bool]:
        """Structured ranking breakdown for logging and audit."""
        breakdown = candidate.score_breakdown
        quality = candidate.sentiment.catalyst_quality
        result: dict[str, float | str | bool] = {
            "symbol": candidate.stock.symbol,
            "final_score": candidate.final_score,
            "technical_score": candidate.technical_score,
            "catalyst_score": candidate.catalyst_score,
            "effective_catalyst_score": candidate.effective_catalyst_score or candidate.catalyst_score,
            "sentiment_score": candidate.news_score,
            "confidence_score": candidate.confidence_score,
            "catalyst_type": candidate.sentiment.primary_catalyst_type.value,
            "direct_company_news": candidate.sentiment.direct_company_news,
        }
        if quality:
            result["catalyst_magnitude"] = quality.magnitude.value
            result["magnitude_score"] = quality.magnitude_score
            result["materiality_score"] = quality.materiality_score
            result["tradability_score"] = quality.tradability_score
        impact = candidate.sentiment.catalyst_impact
        if impact:
            result["composite_impact_score"] = candidate.composite_impact_score
            for name, score in impact.dimension_items():
                result[f"impact_{name}"] = score
        if breakdown:
            result.update(
                {
                    "weighted_catalyst": breakdown.weighted_catalyst,
                    "weighted_magnitude": breakdown.weighted_magnitude,
                    "weighted_materiality": breakdown.weighted_materiality,
                    "weighted_tradability": breakdown.weighted_tradability,
                    "weighted_technical": breakdown.weighted_technical,
                    "weighted_sentiment": breakdown.weighted_sentiment,
                    "weighted_confidence": breakdown.weighted_confidence,
                }
            )
        return result

    @staticmethod
    def _technical_summary(candidate: TradingCandidate) -> str:
        technical = candidate.technical
        if technical.ema20 >= technical.ema50 and technical.price_momentum >= 0:
            return "Strong uptrend above EMA20 and EMA50 with positive momentum."
        if technical.ema20 >= technical.ema50:
            return "Trend remains constructive above key moving averages."
        if technical.relative_volume >= 1.5:
            return "Volume expansion suggests increased participation."
        return "Mixed technical setup; monitor opening price action."

    @staticmethod
    def _risk_factors(candidate: TradingCandidate) -> list[str]:
        risks: list[str] = []
        if not candidate.sentiment.direct_company_news:
            risks.append("News reference is not a direct company-specific catalyst.")
        if candidate.sentiment.primary_catalyst_type in WEAK_CATALYST_TYPES:
            risks.append(
                f"Weak catalyst type: {candidate.sentiment.primary_catalyst_type.value}."
            )
        quality = candidate.sentiment.catalyst_quality
        if quality and quality.tradability_score < 25:
            risks.append(f"Low tradability score ({quality.tradability_score:.0f}).")
        if candidate.technical.price_momentum >= 5:
            risks.append(f"Already gained {candidate.technical.price_momentum:.1f}% recently.")
        if candidate.technical.relative_volume >= 2.5:
            risks.append("Elevated relative volume may indicate crowded positioning.")
        if candidate.sentiment.direction == SentimentDirection.BEARISH:
            risks.append("Bearish sentiment detected in linked news.")
        if not risks:
            risks.append("Standard pre-market gap and opening volatility risk.")
        return risks

    @staticmethod
    def _reason_for_ranking(candidate: TradingCandidate) -> str:
        breakdown = candidate.score_breakdown
        quality = candidate.sentiment.catalyst_quality

        if breakdown and candidate.event_score is not None:
            wfresh = candidate.freshness_score * 0.05
            parts = [
                f"Final {breakdown.final:.0f}",
                f"event {breakdown.weighted_catalyst:.1f}",
                f"technical {breakdown.weighted_technical:.1f}",
                f"liquidity {breakdown.weighted_tradability:.1f}",
                f"sentiment {breakdown.weighted_sentiment:.1f}",
                f"freshness {wfresh:.1f}",
            ]
            base = " = ".join([parts[0], " + ".join(parts[1:])]) + "."
            mag_w = breakdown.weighted_magnitude
            mat_w = breakdown.weighted_materiality
            if mag_w > 0 or mat_w > 0:
                base = (
                    f"{base} Event blend includes magnitude {mag_w:.1f} "
                    f"and materiality {mat_w:.1f} (audit weights)."
                )
            if quality and quality.magnitude in {
                CatalystMagnitude.VERY_HIGH,
                CatalystMagnitude.HIGH,
            }:
                return f"{base} Strong {quality.magnitude.value} catalyst with tradable setup."
            return base

        if breakdown and breakdown.weighted_catalyst > 0:
            mag_w, mat_w = CandidateExplanationBuilder._display_magnitude_materiality(
                candidate, breakdown
            )
            parts = [
                f"Final {breakdown.final:.0f}",
                f"catalyst {breakdown.weighted_catalyst:.1f}",
                f"magnitude {mag_w:.1f}",
                f"materiality {mat_w:.1f}",
                f"tradability {breakdown.weighted_tradability:.1f}",
                f"technical {breakdown.weighted_technical:.1f}",
            ]
            base = " = ".join([parts[0], " + ".join(parts[1:])]) + "."
            if quality and quality.magnitude in {
                CatalystMagnitude.VERY_HIGH,
                CatalystMagnitude.HIGH,
            }:
                return f"{base} Strong {quality.magnitude.value} catalyst with tradable setup."
            return base
        catalyst = candidate.sentiment.primary_catalyst_type
        if catalyst in {
            CatalystType.ORDER_WIN,
            CatalystType.LARGE_CONTRACT,
            CatalystType.EARNINGS_BEAT,
            CatalystType.EARNINGS,
        }:
            return "Strong catalyst plus supportive technical setup."
        if (candidate.effective_catalyst_score or candidate.catalyst_score) >= candidate.technical_score:
            return "Catalyst strength leads ranking; technicals provide confirmation."
        return "Technical strength leads; catalyst provides context."

    @staticmethod
    def _display_magnitude_materiality(
        candidate: TradingCandidate, breakdown: ScoreBreakdown
    ) -> tuple[float, float]:
        """Return weighted magnitude/materiality, recomputing when breakdown zeros."""
        mag_w = breakdown.weighted_magnitude
        mat_w = breakdown.weighted_materiality
        if mag_w > 0 and mat_w > 0:
            return mag_w, mat_w
        quality = candidate.sentiment.catalyst_quality
        mag = candidate.magnitude_score or (quality.magnitude_score if quality else 50.0)
        mat = candidate.materiality_score or (quality.materiality_score if quality else 50.0)
        audit = RankingWeightV2Config()
        if mag_w <= 0:
            mag_w = mag * audit.magnitude
        if mat_w <= 0:
            mat_w = mat * audit.materiality
        return mag_w, mat_w
