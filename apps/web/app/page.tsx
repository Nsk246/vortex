import { Shell } from "@/components/Shell";
import { UploadCase } from "@/components/UploadCase";

export default function Home() {
  return (
    <Shell>
      <div className="mx-auto grid min-h-screen max-w-7xl gap-6 p-5 md:p-8 xl:grid-cols-[1fr_420px]">
        <section className="flex flex-col justify-between border border-line bg-ink/70 p-6 md:p-10">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-mint/70">VORTEX</p>
            <h1 className="mt-5 max-w-4xl text-5xl font-semibold leading-tight md:text-7xl">
              Multi-agent deepfake tribunal for enterprise media forensics.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              Upload contested media, stream the jurors as they inspect visual, acoustic, and contextual evidence, then preserve a structured audit trail for every verdict.
            </p>
          </div>
          <div className="mt-10 grid gap-3 md:grid-cols-3">
            {["Visual ensemble", "Wav2Vec anti-spoofing", "Weighted judge consensus"].map((item) => (
              <div key={item} className="border border-line bg-panel p-4 text-sm text-slate-300">{item}</div>
            ))}
          </div>
        </section>
        <UploadCase />
      </div>
    </Shell>
  );
}

