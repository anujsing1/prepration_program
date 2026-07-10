"""Build NEW CATALYSTS DISCOVERED report section."""

from morning_trading_agent.domain.entities.catalyst_taxonomy import PendingCatalystSummary


class PendingCatalystReportBuilder:
    """Formats pending catalyst discoveries for watchlist reports."""

    def build(self, discoveries: list[PendingCatalystSummary]) -> str:
        if not discoveries:
            return ""
        lines = [
            "## NEW CATALYSTS DISCOVERED",
            "",
            "| Code | Occurrences | Confidence | Example Headline |",
            "|------|-------------|------------|------------------|",
        ]
        for item in discoveries:
            headline = item.example_headline.replace("|", "\\|")[:120]
            lines.append(
                f"| {item.proposed_code} | {item.occurrence_count} | "
                f"{item.confidence:.2f} | {headline} |"
            )
        return "\n".join(lines)
