"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [organization, setOrganization] = useState("");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    if (!email.trim()) {
      setError("Email is required.");
      return;
    }
    if (password.length < 10) {
      setError("Password must be at least 10 characters.");
      return;
    }
    if (mode === "register") {
      if (fullName.trim().length < 2) {
        setError("Full name must be at least 2 characters.");
        return;
      }
      if (organization.trim().length < 2) {
        setError("Organization must be at least 2 characters.");
        return;
      }
    }
    try {
      if (mode === "login") await login(email.trim(), password);
      else await register(email.trim(), password, fullName.trim(), organization.trim());
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center p-5">
      <form onSubmit={submit} className="court-panel w-full max-w-md p-6">
        <p className="text-xs uppercase tracking-[0.32em] text-mint/70">VORTEX Access</p>
        <h1 className="mt-3 text-3xl font-semibold">{mode === "login" ? "Sign in" : "Create workspace"}</h1>
        <div className="mt-6 grid grid-cols-2 border border-line">
          <button type="button" onClick={() => setMode("register")} className={`py-2 ${mode === "register" ? "bg-mint text-ink" : ""}`}>Register</button>
          <button type="button" onClick={() => setMode("login")} className={`py-2 ${mode === "login" ? "bg-mint text-ink" : ""}`}>Login</button>
        </div>
        {mode === "register" && (
          <>
            <input className="mt-4 w-full border border-line bg-ink px-3 py-3" placeholder="Full name" value={fullName} onChange={(event) => setFullName(event.target.value)} />
            <input className="mt-3 w-full border border-line bg-ink px-3 py-3" placeholder="Organization" value={organization} onChange={(event) => setOrganization(event.target.value)} />
          </>
        )}
        <input className="mt-3 w-full border border-line bg-ink px-3 py-3" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} />
        <input className="mt-3 w-full border border-line bg-ink px-3 py-3" type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} />
        {error && <p className="mt-4 border border-signal/40 bg-signal/10 p-3 text-sm">{error}</p>}
        <button className="mt-5 w-full bg-mint px-4 py-3 font-semibold text-ink">Continue</button>
      </form>
    </main>
  );
}
