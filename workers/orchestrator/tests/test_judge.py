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


def test_single_suspicious_juror_prevents_authentic_label():
    verdict = weighted_consensus(
        [
            JurorDecision("visual", 0.52, 0.8, {}, ""),
            JurorDecision("acoustic", 0.05, 0.2, {}, ""),
        ]
    )
    assert verdict.label == "inconclusive"


def test_provider_fallback_prevents_authentic_label():
    verdict = weighted_consensus(
        [
            JurorDecision("visual", 0.1, 0.8, {}, ""),
            JurorDecision("context", 0.5, 0.2, {"provider_error": "RateLimitError"}, ""),
        ]
    )
    assert verdict.label == "inconclusive"


def test_visual_signal_can_mark_synthetic_suspected():
    verdict = weighted_consensus(
        [
            JurorDecision("visual", 0.58, 0.99, {}, ""),
            JurorDecision("acoustic", 0.07, 0.15, {}, ""),
            JurorDecision("context", 0.5, 0.2, {"provider_error": "RateLimitError"}, ""),
        ]
    )
    assert verdict.label == "synthetic_suspected"
