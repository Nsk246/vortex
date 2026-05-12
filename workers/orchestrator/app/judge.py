from dataclasses import dataclass


@dataclass(frozen=True)
class JurorDecision:
    juror_name: str
    confidence: float
    weight: float
    quality: dict
    rationale: str


@dataclass(frozen=True)
class Verdict:
    final_confidence: float
    label: str
    disagreement_score: float
    reexamination_triggered: bool
    rationale: str
    weights: dict[str, float]


def weighted_consensus(decisions: list[JurorDecision], disagreement_threshold: float = 0.45) -> Verdict:
    if not decisions:
        raise ValueError("At least one juror decision is required")
    total_weight = sum(max(decision.weight, 0.0) for decision in decisions)
    if total_weight <= 0:
        raise ValueError("Total juror weight must be positive")
    final = sum(decision.weight * decision.confidence for decision in decisions) / total_weight
    confidences = [decision.confidence for decision in decisions]
    max_confidence = max(confidences)
    provider_fallback = any(decision.quality.get("provider_error") for decision in decisions)
    disagreement = max(confidences) - min(confidences)
    if final >= 0.75:
        label = "deepfake_high_confidence"
    elif final >= 0.55:
        label = "deepfake_likely"
    elif final >= 0.48 and max_confidence >= 0.55:
        label = "synthetic_suspected"
    elif final >= 0.35 or max_confidence >= 0.45 or provider_fallback:
        label = "inconclusive"
    else:
        label = "likely_authentic"
    reexam = disagreement >= disagreement_threshold
    weights = {decision.juror_name: decision.weight for decision in decisions}
    rationale = (
        f"Judge computed weighted consensus from {len(decisions)} jurors. "
        f"Final manipulation confidence is {final:.3f}; disagreement is {disagreement:.3f}."
    )
    if provider_fallback:
        rationale += " At least one juror used fallback reasoning, so authenticity is not asserted from missing context."
    if reexam:
        rationale += " Disagreement exceeded threshold, so a re-examination round is required."
    return Verdict(
        final_confidence=final,
        label=label,
        disagreement_score=disagreement,
        reexamination_triggered=reexam,
        rationale=rationale,
        weights=weights,
    )
