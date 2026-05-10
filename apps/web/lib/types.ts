export type CaseSummary = {
  id: string;
  title: string;
  status: string;
  risk_score: number | null;
  verdict_label: string | null;
  created_at: string;
};

export type AuditEvent = {
  id?: string;
  event_type: string;
  actor: string;
  message: string;
  payload: Record<string, unknown>;
  created_at?: string;
};

export type Verdict = {
  final_confidence: number;
  label: string;
  disagreement_score: number;
  reexamination_triggered: boolean;
  rationale: string;
  weights: Record<string, number>;
};

export type CaseDetail = CaseSummary & {
  media_assets: Array<{
    id: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    sha256: string;
  }>;
  audit_events: AuditEvent[];
  verdict: Verdict | null;
};

