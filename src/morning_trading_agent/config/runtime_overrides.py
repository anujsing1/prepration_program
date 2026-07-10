"""Apply per-run session overrides without mutating .env."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from morning_trading_agent.config.settings import Settings

_SESSION_TO_FORCE: dict[str, str] = {
    "premarket": "PREMARKET",
    "pre_market": "PRE_MARKET",
    "intraday": "INTRADAY",
    "postmarket": "POSTMARKET",
    "post_market": "POST_MARKET",
    "auto": "",
}


@dataclass(frozen=True)
class RuntimeOverrides:
    """CLI/runtime overrides for a single pipeline invocation."""

    session: str | None = None
    run_at: datetime | None = None


def normalize_session_choice(session: str | None) -> str | None:
    """Normalize session CLI value; returns None for auto/empty."""
    if session is None:
        return None
    key = session.strip().lower().replace("-", "_")
    if key in {"", "auto"}:
        return None
    if key not in _SESSION_TO_FORCE:
        valid = "premarket, intraday, postmarket, auto"
        raise ValueError(f"Invalid session {session!r}. Expected one of: {valid}")
    return key


def apply_runtime_overrides(
    settings: Settings,
    overrides: RuntimeOverrides,
) -> Settings:
    """Return settings copy with per-run session/datetime overrides."""
    app_updates: dict[str, object] = {}

    if overrides.session is not None:
        session_key = normalize_session_choice(overrides.session)
        app_updates["force_session"] = (
            _SESSION_TO_FORCE[session_key] if session_key is not None else ""
        )

    if overrides.run_at is not None:
        app_updates["run_datetime_override"] = overrides.run_at.isoformat()

    if not app_updates:
        return settings

    return settings.model_copy(
        update={"app": settings.app.model_copy(update=app_updates)}
    )


def describe_runtime(settings: Settings) -> str:
    """Human-readable summary of resolved session for CLI output."""
    runtime = settings.resolved_runtime
    return (
        f"session={runtime.detected_session.value}, "
        f"strategy={runtime.effective_strategy}, "
        f"source={runtime.run_datetime_source}"
    )
