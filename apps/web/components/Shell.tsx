import Link from "next/link";
import { Activity, Gauge, Settings, ShieldCheck } from "lucide-react";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen">
      <aside className="fixed left-0 top-0 hidden h-full w-20 border-r border-line bg-ink/90 p-4 md:block">
        <div className="mb-10 flex h-11 w-11 items-center justify-center border border-mint/40 bg-mint/10 text-mint">
          <ShieldCheck size={22} />
        </div>
        <nav className="flex flex-col gap-4 text-slate-400">
          <Link className="flex h-11 w-11 items-center justify-center hover:text-mint" href="/dashboard" title="Dashboard">
            <Gauge size={21} />
          </Link>
          <Link className="flex h-11 w-11 items-center justify-center hover:text-mint" href="/" title="Tribunal">
            <Activity size={21} />
          </Link>
          <Link className="flex h-11 w-11 items-center justify-center hover:text-mint" href="/settings" title="Settings">
            <Settings size={21} />
          </Link>
        </nav>
      </aside>
      <section className="md:pl-20">{children}</section>
    </main>
  );
}

