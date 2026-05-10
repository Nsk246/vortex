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
    disagreement = max(confidences) - min(confidences)
    label = "deepfake_high_confidence" if final >= 0.75 else "deepfake_likely" if final >= 0.55 else "inconclusive" if final >= 0.40 else "likely_authentic"
    reexam = disagreement >= disagreement_threshold
    weights = {decision.juror_name: decision.weight for decision in decisions}
    rationale = (
        f"Judge computed weighted consensus from {len(decisions)} jurors. "
        f"Final manipulation confidence is {final:.3f}; disagreement is {disagreement:.3f}."
    )
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

