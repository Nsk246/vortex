"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createCase, getToken, uploadMedia } from "@/lib/api";
import { UploadCloud } from "lucide-react";

export function UploadCase() {
  const router = useRouter();
  const [title, setTitle] = useState("Election interview authenticity review");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setHasToken(Boolean(getToken()));
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a video or audio file.");
      return;
    }
    setBusy(true);
    setError("");
    setStatus("Creating tribunal case");
    try {
      const created = await createCase(title);
      setStatus("Uploading evidence to secure object storage");
      await uploadMedia(created.id, file);
      setStatus("Opening live tribunal room");
      router.push(`/cases/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="court-panel p-5">
      <div className="mb-5">
        <p className="text-xs uppercase tracking-[0.28em] text-mint/70">New Case</p>
        <h2 className="mt-2 text-2xl font-semibold">Admit evidence to tribunal</h2>
      </div>
      <label className="mb-4 block">
        <span className="mb-2 block text-sm text-slate-300">Case title</span>
        <input className="w-full border border-line bg-ink px-3 py-3 outline-none focus:border-mint" value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <label className="grid min-h-52 cursor-pointer place-items-center border border-dashed border-mint/40 bg-mint/5 p-6 text-center">
        <input className="hidden" type="file" accept="video/mp4,video/quicktime,audio/mpeg,audio/wav" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <span>
          <UploadCloud className="mx-auto mb-4 text-mint" size={36} />
          <span className="block font-medium">{file ? file.name : "Drop or select MP4, MOV, WAV, or MP3 evidence"}</span>
          <span className="mt-2 block text-sm text-slate-400">Free tier limits are enforced server-side.</span>
        </span>
      </label>
      {!hasToken && (
        <p className="mt-4 border border-mint/30 bg-mint/10 p-3 text-sm text-mint">
          Create or enter a workspace before uploading. <Link className="font-semibold underline" href="/login">Open access</Link>
        </p>
      )}
      {status && <p className="mt-4 border border-line bg-ink/70 p-3 text-sm text-slate-200">{status}</p>}
      {error && <p className="mt-4 border border-signal/40 bg-signal/10 p-3 text-sm text-red-100">{error}</p>}
      <button disabled={busy} className="mt-5 w-full bg-mint px-4 py-3 font-semibold text-ink disabled:opacity-50">
        {busy ? status || "Uploading evidence" : "Create tribunal case"}
      </button>
    </form>
  );
}
