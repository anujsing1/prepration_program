"""Factory for catalyst quality enrichment services."""

from morning_trading_agent.application.services.catalyst.catalyst_impact_assessment_service import (
    CatalystImpactAssessmentService,
)
from morning_trading_agent.application.services.catalyst.candidate_impact_scoring_service import (
    CandidateImpactScoringService,
)
from morning_trading_agent.application.services.catalyst.catalyst_tradability_service import (
    CatalystTradabilityService,
)
from morning_trading_agent.application.services.catalyst.tradability_profile_service import (
    TradabilityProfileService,
)
from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.application.services.catalyst_quality.catalyst_escalation_service import (
    CatalystEscalationService,
)
from morning_trading_agent.application.services.catalyst_quality.catalyst_magnitude_service import (
    CatalystMagnitudeService,
)
from morning_trading_agent.application.services.catalyst_quality.catalyst_quality_enrichment_service import (
    CatalystQualityEnrichmentService,
)
from morning_trading_agent.application.services.catalyst_quality.effective_catalyst_score_service import (
    EffectiveCatalystScoreService,
)
from morning_trading_agent.application.services.catalyst_quality.materiality_service import (
    MaterialityService,
)
from morning_trading_agent.application.services.catalyst_quality.tradability_service import (
    TradabilityService,
)
from morning_trading_agent.config.settings import Settings


class CatalystQualityFactory:
    """Creates catalyst quality services from settings."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_tradability_service(self) -> CatalystTradabilityService:
        """Build catalyst tradability policy assessment service."""
        return CatalystTradabilityService()

    def create_tradability_profile_service(self) -> TradabilityProfileService:
        """Build canonical tradability profile synthesis service."""
        return TradabilityProfileService(tradability=self.create_tradability_service())

    def create_impact_scoring_service(self) -> CandidateImpactScoringService:
        """Build composite impact scoring service."""
        return CandidateImpactScoringService(
            weight_config=self._settings.impact_weight_config,
        )

    def create_impact_assessment_service(
        self,
        *,
        stats_service=None,
    ) -> CatalystImpactAssessmentService:
        """Build impact assessment service (replaces tradability gate)."""
        return CatalystImpactAssessmentService(
            impact_scoring=self.create_impact_scoring_service(),
            stats_service=stats_service,
        )

    def create_enrichment_service(
        self, *, scoring_service: CatalystScoringService | None = None
    ) -> CatalystQualityEnrichmentService:
        """Build orchestrator with configured sub-services."""
        non_tradable = self._settings.non_tradable_catalyst_config
        return CatalystQualityEnrichmentService(
            profile_service=self.create_tradability_profile_service(),
            magnitude_service=CatalystMagnitudeService(
                config=self._settings.catalyst_magnitude_config
            ),
            materiality_service=MaterialityService(
                config=self._settings.materiality_config,
                non_tradable_config=non_tradable,
            ),
            escalation_service=CatalystEscalationService(
                config=self._settings.catalyst_escalation_config
            ),
            tradability_service=TradabilityService(
                config=self._settings.tradability_config,
                non_tradable_config=non_tradable,
                rejection_config=self._settings.catalyst_rejection_config,
                scoring_service=scoring_service,
            ),
            effective_catalyst_service=EffectiveCatalystScoreService(
                broker_config=self._settings.broker_rating_config,
                score_config=self._settings.catalyst_score_config,
            ),
            non_tradable_config=non_tradable,
        )
