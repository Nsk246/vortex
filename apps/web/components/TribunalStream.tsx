"use client";

import { useEffect, useMemo, useState } from "react";
import { BrainCircuit, CheckCircle2, CircleDashed, Scale, TriangleAlert, Waves } from "lucide-react";
import { caseStreamUrl, getCase, runCase } from "@/lib/api";
import type { AuditEvent, CaseDetail } from "@/lib/types";

const jurors = [
  { id: "visual", label: "Visual Juror", icon: BrainCircuit },
  { id: "acoustic", label: "Acoustic Juror", icon: Waves },
  { id: "context", label: "Context Juror", icon: TriangleAlert },
  { id: "judge", label: "Judge", icon: Scale }
];

type EvidencePayload = {
  confidence?: number;
  weight?: number;
  quality?: Record<string, unknown>;
  evidence?: Array<Record<string, unknown>>;
  label?: string;
  final_confidence?: number;
  disagreement_score?: number;
  weights?: Record<string, number>;
};

function asPayload(event?: AuditEvent): EvidencePayload {
  return (event?.payload ?? {}) as EvidencePayload;
}

function asNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function percent(value: unknown) {
  const number = asNumber(value);
  return number === null ? "Pending" : `${Math.round(number * 100)}%`;
}

function fixed(value: unknown, digits = 2) {
  const number = asNumber(value);
  return number === null ? "Pending" : number.toFixed(digits);
}

function evidenceRows(payload: EvidencePayload) {
  return Array.isArray(payload.evidence) ? payload.evidence : [];
}

function EvidenceCanvas({ caseData, latestByActor }: { caseData: CaseDetail; latestByActor: Map<string, AuditEvent> }) {
  const visual = asPayload(latestByActor.get("visual"));
  const acoustic = asPayload(latestByActor.get("acoustic"));
  const context = asPayload(latestByActor.get("context"));
  const judge = asPayload(latestByActor.get("judge"));
  const visualRows = evidenceRows(visual);
  const audioRows = evidenceRows(acoustic);
  const sampledFrames = asNumber(visual.quality?.sampled_frames) ?? 96;
  const frameScores = new Map<number, number>();
  for (const row of visualRows) {
    const index = asNumber(row.frame_index);
    const score = asNumber(row.combined_score);
    if (index !== null && score !== null) frameScores.set(index, score);
  }
  const heatCells = Array.from({ length: Math.min(Math.max(sampledFrames, 24), 96) }, (_, index) => {
    const score = frameScores.get(index) ?? 0;
    const opacity = score > 0 ? 0.2 + Math.min(score, 1) * 0.8 : 0.08;
    return { index, score, opacity };
  });
  const verdictConfidence = judge.final_confidence ?? caseData.verdict?.final_confidence ?? caseData.risk_score;

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-4">
        <div className="border border-line bg-ink/50 p-3">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Visual</p>
          <p className="mt-2 text-2xl font-semibold text-mint">{percent(visual.confidence)}</p>
          <p className="mt-1 text-xs text-slate-400">weight {fixed(visual.weight)}</p>
        </div>
        <div className="border border-line bg-ink/50 p-3">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Acoustic</p>
          <p className="mt-2 text-2xl font-semibold text-mint">{percent(acoustic.confidence)}</p>
          <p className="mt-1 text-xs text-slate-400">weight {fixed(acoustic.weight)}</p>
        </div>
        <div className="border border-line bg-ink/50 p-3">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Context</p>
          <p className="mt-2 text-2xl font-semibold text-amber">{percent(context.confidence)}</p>
          <p className="mt-1 text-xs text-slate-400">{context.quality?.provider_error ? "fallback" : "reasoning"}</p>
        </div>
        <div className="border border-line bg-ink/50 p-3">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Judge</p>
          <p className="mt-2 text-2xl font-semibold text-amber">{percent(verdictConfidence)}</p>
          <p className="mt-1 text-xs text-slate-400">{caseData.verdict?.label?.replaceAll("_", " ") ?? caseData.status}</p>
        </div>
      </div>

      <div className="border border-line bg-black/30 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-mint/70">Frame Heatmap</p>
            <p className="mt-1 text-sm text-slate-400">{visualRows.length ? `${visualRows.length} high-signal frames surfaced` : "Waiting for visual juror output"}</p>
          </div>
          <span className="border border-line px-2 py-1 text-xs text-slate-400">{Math.round(sampledFrames)} sampled</span>
        </div>
        <div className="grid grid-cols-12 gap-1">
          {heatCells.map((cell) => (
            <div
              key={cell.index}
              className="aspect-square border border-line/60"
              title={`Frame ${cell.index}: ${percent(cell.score)}`}
              style={{ backgroundColor: cell.score > 0 ? `rgba(232,100,82,${cell.opacity})` : "rgba(126,230,184,0.08)" }}
            />
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="border border-line bg-ink/40 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-mint/70">Top Visual Evidence</p>
          <div className="mt-4 space-y-3">
            {visualRows.length === 0 && <p className="text-sm text-slate-400">No frame evidence has arrived yet.</p>}
            {visualRows.map((row, index) => {
              const frameIndex = asNumber(row.frame_index) ?? index;
              const combined = asNumber(row.combined_score) ?? 0;
              const face = asNumber(row.face_detector_score) ?? 0;
              const general = asNumber(row.general_detector_score) ?? 0;
              return (
                <div key={`${frameIndex}-${index}`}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="text-slate-200">Frame {frameIndex}</span>
                    <span className="text-amber">{percent(combined)}</span>
                  </div>
                  <div className="h-2 bg-black/40">
                    <div className="h-2 bg-signal" style={{ width: `${Math.max(4, combined * 100)}%` }} />
                  </div>
                  <p className="mt-1 text-xs text-slate-500">face {percent(face)} · general {percent(general)}</p>
                </div>
              );
            })}
          </div>
        </div>

        <div className="border border-line bg-ink/40 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-mint/70">Audio Windows</p>
          <div className="mt-4 flex h-32 items-end gap-2 border-b border-line pb-2">
            {(audioRows.length ? audioRows : Array.from({ length: 8 }, (_, index) => ({ window_index: index, fake_probability: 0 }))).map((row, index) => {
              const score = asNumber(row.fake_probability) ?? 0;
              const height = audioRows.length ? Math.max(8, score * 100) : 12 + index * 5;
              return (
                <div
                  key={`${asNumber(row.window_index) ?? index}-${index}`}
                  className={audioRows.length ? "w-full bg-amber" : "w-full bg-mint/20"}
                  title={`Window ${asNumber(row.window_index) ?? index}: ${percent(score)}`}
                  style={{ height: `${height}%`, opacity: audioRows.length ? 0.85 : 0.25 }}
                />
              );
            })}
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-slate-400">
            <span>windows {fixed(acoustic.quality?.window_count, 0)}</span>
            <span>coverage {percent(acoustic.quality?.coverage)}</span>
            <span>rms {fixed(acoustic.quality?.rms_proxy, 3)}</span>
            <span>clip {percent(acoustic.quality?.clipping_ratio)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function TribunalStream({ initialCase }: { initialCase: CaseDetail }) {
  const [caseData, setCaseData] = useState(initialCase);
  const [events, setEvents] = useState<AuditEvent[]>(initialCase.audit_events);
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState("");

  useEffect(() => {
    const socket = new WebSocket(caseStreamUrl(initialCase.id));
    socket.onmessage = (message) => {
      const event = JSON.parse(message.data) as AuditEvent;
      setEvents((current) => [...current, event]);
      if (event.event_type === "judge.verdict") {
        getCase(initialCase.id).then(setCaseData).catch(() => undefined);
        setIsRunning(false);
      }
      if (event.event_type === "tribunal.failed") {
        getCase(initialCase.id).then(setCaseData).catch(() => undefined);
        setIsRunning(false);
      }
    };
    return () => socket.close();
  }, [initialCase.id]);

  useEffect(() => {
    setCaseData(initialCase);
    setEvents(initialCase.audit_events);
  }, [initialCase]);

  useEffect(() => {
    if (!["queued", "processing"].includes(caseData.status)) return;
    const refresh = async () => {
      try {
        const freshCase = await getCase(caseData.id);
        setCaseData(freshCase);
        setEvents(freshCase.audit_events);
        if (["complete", "failed"].includes(freshCase.status)) {
          setIsRunning(false);
          setRunError("");
        }
      } catch {
        // WebSocket remains the primary live path; polling is only a stale-state backup.
      }
    };
    void refresh();
    const interval = window.setInterval(refresh, 5000);
    return () => window.clearInterval(interval);
  }, [caseData.id, caseData.status]);

  const latestByActor = useMemo(() => {
    const map = new Map<string, AuditEvent>();
    for (const event of events) map.set(event.actor, event);
    return map;
  }, [events]);

  async function start() {
    if (isRunning || caseData.status === "complete" || caseData.status === "processing") return;
    if (caseData.status === "queued" && events.length > 0) return;
    setIsRunning(true);
    setRunError("");
    setCaseData((current) => ({ ...current, status: "queued" }));
    try {
      await runCase(caseData.id);
      setCaseData((current) => ({ ...current, status: "processing" }));
    } catch (err) {
      setIsRunning(false);
      setRunError(err instanceof Error ? err.message : "Could not start tribunal");
      getCase(caseData.id).then(setCaseData).catch(() => undefined);
    }
  }

  useEffect(() => {
    if (caseData.status === "uploaded" && !isRunning && events.length === 0) {
      void start();
    }
  }, [caseData.status, events.length, isRunning]);

  const canRetryQueued = caseData.status === "queued" && events.length === 0;
  const startDisabled = isRunning || caseData.status === "complete" || caseData.status === "processing" || (caseData.status === "queued" && !canRetryQueued);

  return (
    <div className="grid gap-5 xl:grid-cols-[360px_1fr_360px]">
      <section className="court-panel p-5">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-mint/70">Tribunal</p>
            <h1 className="mt-2 text-2xl font-semibold">{caseData.title}</h1>
          </div>
          <button
            onClick={start}
            disabled={startDisabled}
            className="border border-mint/40 bg-mint px-4 py-2 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-40"
          >
            {caseData.status === "complete"
              ? "Complete"
              : isRunning
                ? "Starting"
                : caseData.status === "processing"
                  ? "Running"
                  : canRetryQueued
                    ? "Retry start"
                    : "Start"}
          </button>
        </div>
        {runError && <p className="mb-4 border border-signal/40 bg-signal/10 p-3 text-sm text-red-100">{runError}</p>}
        <div className="space-y-3">
          {jurors.map((juror) => {
            const event = latestByActor.get(juror.id);
            const Icon = juror.icon;
            return (
              <div key={juror.id} className="border border-line bg-ink/40 p-4">
                <div className="flex items-center gap-3">
                  <Icon className="text-mint" size={20} />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{juror.label}</p>
                    <p className="truncate text-sm text-slate-400">{event?.message ?? "Awaiting evidence"}</p>
                  </div>
                  {event ? <CheckCircle2 className="text-mint" size={18} /> : <CircleDashed className="text-slate-500" size={18} />}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="court-panel min-h-[620px] p-5">
        <div className="mb-4 flex items-center justify-between border-b border-line pb-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-mint/70">Evidence Canvas</p>
            <h2 className="mt-2 text-xl font-semibold">Frame, waveform, and anomaly evidence</h2>
          </div>
          <span className="border border-line px-3 py-1 text-sm text-slate-300">{caseData.status}</span>
        </div>
        <EvidenceCanvas caseData={caseData} latestByActor={latestByActor} />
      </section>

      <section className="court-panel p-5">
        <p className="text-xs uppercase tracking-[0.28em] text-mint/70">ThinkTrace Audit</p>
        <div className="mt-4 max-h-[520px] space-y-3 overflow-auto pr-2">
          {events.map((event, index) => (
            <article key={`${event.event_type}-${index}`} className="border border-line bg-ink/40 p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-mint">{event.actor}</span>
                <span className="text-xs text-slate-500">{event.event_type}</span>
              </div>
              <p className="text-sm leading-6 text-slate-200">{event.message}</p>
            </article>
          ))}
        </div>
        {caseData.verdict && (
          <div className="mt-5 border border-amber/40 bg-amber/10 p-4">
            <p className="text-sm uppercase tracking-[0.22em] text-amber">Final Verdict</p>
            <p className="mt-2 text-2xl font-semibold">{caseData.verdict.label.replaceAll("_", " ")}</p>
            <p className="mt-2 text-sm text-slate-300">{Math.round(caseData.verdict.final_confidence * 100)}% manipulation confidence</p>
          </div>
        )}
      </section>
    </div>
  );
}
