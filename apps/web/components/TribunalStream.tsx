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

export function TribunalStream({ initialCase }: { initialCase: CaseDetail }) {
  const [caseData, setCaseData] = useState(initialCase);
  const [events, setEvents] = useState<AuditEvent[]>(initialCase.audit_events);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const socket = new WebSocket(caseStreamUrl(initialCase.id));
    socket.onmessage = (message) => {
      const event = JSON.parse(message.data) as AuditEvent;
      setEvents((current) => [...current, event]);
      if (event.event_type === "judge.verdict") {
        getCase(initialCase.id).then(setCaseData).catch(() => undefined);
        setIsRunning(false);
      }
    };
    return () => socket.close();
  }, [initialCase.id]);

  const latestByActor = useMemo(() => {
    const map = new Map<string, AuditEvent>();
    for (const event of events) map.set(event.actor, event);
    return map;
  }, [events]);

  async function start() {
    setIsRunning(true);
    await runCase(caseData.id);
  }

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
            disabled={isRunning || caseData.status === "complete"}
            className="border border-mint/40 bg-mint px-4 py-2 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-40"
          >
            Start
          </button>
        </div>
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
        <div className="grid h-[520px] place-items-center border border-line bg-black/30">
          <div className="w-full max-w-2xl px-8">
            <div className="mb-8 h-40 border border-mint/20 bg-[linear-gradient(135deg,rgba(126,230,184,.10),rgba(232,100,82,.08))]" />
            <div className="space-y-2">
              {Array.from({ length: 28 }).map((_, index) => (
                <div
                  key={index}
                  className="h-2 bg-mint/20"
                  style={{ width: `${30 + ((index * 17) % 64)}%`, opacity: 0.25 + ((index % 6) * 0.1) }}
                />
              ))}
            </div>
          </div>
        </div>
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

