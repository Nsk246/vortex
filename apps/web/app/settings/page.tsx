import { Shell } from "@/components/Shell";

export default function SettingsPage() {
  return (
    <Shell>
      <div className="mx-auto max-w-4xl p-5 md:p-8">
        <p className="text-xs uppercase tracking-[0.32em] text-mint/70">Governance</p>
        <h1 className="mt-3 text-4xl font-semibold">Workspace settings</h1>
        <div className="court-panel mt-6 p-5">
          <p className="text-lg font-semibold">Model license gate</p>
          <p className="mt-2 text-slate-300">
            Production workers require approved visual and acoustic model licenses before inference starts.
          </p>
        </div>
      </div>
    </Shell>
  );
}

