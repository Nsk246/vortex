from app.judge import JurorDecision, weighted_consensus


def test_weighted_consensus_uses_reliability_weights():
    verdict = weighted_consensus(
        [
            JurorDecision("visual", 0.9, 0.8, {}, ""),
            JurorDecision("acoustic", 0.1, 0.2, {}, ""),
        ]
    )
    assert round(verdict.final_confidence, 2) == 0.74
    assert verdict.label == "deepfake_likely"


def test_disagreement_triggers_reexamination():
    verdict = weighted_consensus(
        [
            JurorDecision("visual", 0.95, 0.7, {}, ""),
            JurorDecision("acoustic", 0.05, 0.7, {}, ""),
        ],
        disagreement_threshold=0.45,
    )
    assert verdict.reexamination_triggered is True
    assert verdict.disagreement_score == 0.8999999999999999

