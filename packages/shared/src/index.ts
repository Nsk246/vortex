export type TribunalEventType =
  | "stream.connected"
  | "tribunal.started"
  | "jurors.queued"
  | "juror.complete"
  | "judge.preliminary"
  | "judge.verdict";

export type JurorName = "visual" | "acoustic" | "context" | "judge";

export type TribunalEvent = {
  case_id: string;
  event_type: TribunalEventType;
  actor: JurorName;
  message: string;
  payload: Record<string, unknown>;
};

export type JurorFinding = {
  juror_name: Exclude<JurorName, "judge">;
  confidence: number;
  weight: number;
  quality: Record<string, unknown>;
  evidence: Array<Record<string, unknown>>;
  rationale: string;
  model_versions: string[];
};

export type JudgeVerdict = {
  final_confidence: number;
  label: "deepfake_high_confidence" | "deepfake_likely" | "inconclusive" | "likely_authentic";
  disagreement_score: number;
  reexamination_triggered: boolean;
  rationale: string;
  weights: Record<string, number>;
};

