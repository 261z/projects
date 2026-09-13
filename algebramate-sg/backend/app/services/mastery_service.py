from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveRecommendation:
    action: str
    difficulty: int
    reason: str


def update_mastery(previous: float, correct: bool, difficulty: int, hints_used: int) -> float:
    signal = (0.10 + difficulty * 0.015) if correct else -(0.12 + difficulty * 0.01)
    signal -= min(hints_used, 3) * 0.025
    return max(0.0, min(1.0, round(previous + signal, 4)))


def recommend_difficulty(current: int, recent_correct: int, recent_incorrect: int, hints_used: int, misconception: str | None = None) -> AdaptiveRecommendation:
    if recent_incorrect >= 2 or misconception in {"prerequisite_gap", "concept_unknown"}:
        return AdaptiveRecommendation("easier", max(1, current - 1), "Recent conceptual difficulty suggests a supported step down.")
    if recent_correct >= 3 and hints_used == 0:
        return AdaptiveRecommendation("harder", min(5, current + 1), "Several independent correct answers suggest readiness for a challenge.")
    return AdaptiveRecommendation("same", current, "Keep practising this skill to build consistency.")
