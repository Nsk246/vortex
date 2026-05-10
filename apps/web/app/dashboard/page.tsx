import { Shell } from "@/components/Shell";

export default function DashboardPage() {
  return (
    <Shell>
      <div className="mx-auto max-w-7xl p-5 md:p-8">
        <p className="text-xs uppercase tracking-[0.32em] text-mint/70">Operations</p>
        <h1 className="mt-3 text-4xl font-semibold">Enterprise dashboard</h1>
        <div className="mt-6 grid gap-4 md:grid-cols-4">
          {[
            ["GPU queue", "Ready"],
            ["Free quota", "5/month"],
            ["Retention", "30 days"],
            ["Audit mode", "Strict"]
          ].map(([label, value]) => (
            <div key={label} className="court-panel p-5">
              <p className="text-sm text-slate-400">{label}</p>
              <p className="mt-2 text-2xl font-semibold">{value}</p>
            </div>
          ))}
        </div>
      </div>
    </Shell>
  );
}

