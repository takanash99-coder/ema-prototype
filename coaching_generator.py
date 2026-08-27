from __future__ import annotations

from models import LegendAnalysisResult


def generate_coaching(result: LegendAnalysisResult) -> str:
    needs_review = [item.item for item in result.items if not item.researcher_confirmed]
    if needs_review:
        return "Researcher confirmation is required before final coaching text is generated."
    return "Use the confirmed motion strategy to create individualized coaching advice."
