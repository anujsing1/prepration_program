"""Prediction Validation Agent — compare prior predictions to today's outcomes."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.memory.market_memory_store import MarketMemoryStore
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import (
    PredictionValidationAnalysis,
    PredictionValidationItem,
    ResearchDeskSnapshot,
)


class PredictionValidationAgent(ResearchDeskAgent):
    """Validate yesterday's predictions against today's NIFTY move."""

    name = "prediction_validation"
    strict = False

    def __init__(self, memory_store: MarketMemoryStore) -> None:
        self._store = memory_store
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["market_memory", "nse_indices"])
        prior = self._store.load_previous_trading_day(snapshot.session_date)
        nifty = snapshot.market_structure.indices.get("NIFTY", {})
        actual_pct = float(nifty.get("momentum_pct", 0.0)) if nifty else 0.0
        actual_label = f"NIFTY {actual_pct:+.2f}%"

        validations: list[PredictionValidationItem] = []
        accuracy_changes: dict[str, float] = {}

        if prior is None:
            health.warnings.append("No prior memory for prediction validation")
            analysis = PredictionValidationAnalysis()
            snapshot = snapshot.model_copy(update={"prediction_validation": analysis})
            health.used_real_data = bool(nifty)
            health.records_processed = 1 if nifty else 0
            return self._finalize_health(snapshot, health)

        predictions = prior.predictions or {}
        opening_bias = str(predictions.get("opening_bias", ""))
        bullish_prob = float(predictions.get("bullish_probability", predictions.get("historical_probability", 0.5)))

        bias_success = _validate_bias(opening_bias, actual_pct)
        validations.append(
            PredictionValidationItem(
                prediction=f"Opening bias: {opening_bias} (bullish prob {bullish_prob:.0%})",
                actual=actual_label,
                success=bias_success,
                agent="GlobalMarketAgent",
            )
        )
        accuracy_changes["GlobalMarketAgent"] = 0.05 if bias_success else -0.05

        regime_pred = str(prior.market_regime.get("regime", prior.market_regime.get("market_regime", "")))
        regime_success = _validate_regime(regime_pred, actual_pct)
        if regime_pred:
            validations.append(
                PredictionValidationItem(
                    prediction=f"Regime: {regime_pred}",
                    actual=actual_label,
                    success=regime_success,
                    agent="MarketRegimeAgent",
                )
            )
            accuracy_changes["MarketRegimeAgent"] = 0.03 if regime_success else -0.03

        fii_pred = str(prior.institutional_summary or "")
        if fii_pred:
            fii_success = (actual_pct > 0 and "buying" in fii_pred.lower()) or (
                actual_pct < 0 and "selling" in fii_pred.lower()
            )
            validations.append(
                PredictionValidationItem(
                    prediction=f"Institutional: {fii_pred[:80]}",
                    actual=actual_label,
                    success=fii_success,
                    agent="InstitutionalFlowAgent",
                )
            )
            accuracy_changes["InstitutionalFlowAgent"] = 0.03 if fii_success else -0.03

        success_rate = sum(1 for v in validations if v.success) / len(validations) if validations else 0.0
        analysis = PredictionValidationAnalysis(
            validations=validations,
            agent_accuracy_changes=accuracy_changes,
            overall_success_rate=round(success_rate, 2),
        )
        snapshot.metadata["prediction_outcomes"] = [v.model_dump() for v in validations]
        snapshot.metadata["agent_accuracy_changes"] = accuracy_changes

        health.used_real_data = True
        health.records_processed = len(validations)
        health.confidence = success_rate
        self._logger.info("prediction_validation_complete", validations=len(validations), success_rate=success_rate)
        snapshot = snapshot.model_copy(update={"prediction_validation": analysis})
        return self._finalize_health(snapshot, health, outputs={"success_rate": success_rate})


def _validate_bias(bias: str, actual_pct: float) -> bool:
    lowered = bias.lower()
    if "gap_up" in lowered or "positive" in lowered:
        return actual_pct > 0.1
    if "gap_down" in lowered or "negative" in lowered:
        return actual_pct < -0.1
    return abs(actual_pct) < 0.5


def _validate_regime(regime: str, actual_pct: float) -> bool:
    bullish_regimes = {"RISK_ON", "ACCUMULATION", "TRENDING", "MOMENTUM", "BREAKOUT"}
    bearish_regimes = {"RISK_OFF", "DISTRIBUTION", "PANIC"}
    upper = regime.upper()
    if upper in bullish_regimes:
        return actual_pct > 0
    if upper in bearish_regimes:
        return actual_pct < 0
    return abs(actual_pct) < 0.8
