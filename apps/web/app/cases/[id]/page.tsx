"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getCase } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { TribunalStream } from "@/components/TribunalStream";
import type { CaseDetail } from "@/lib/types";

export default function CasePage() {
  const params = useParams<{ id: string }>();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getCase(params.id).then(setCaseData).catch((err) => setError(err instanceof Error ? err.message : "Case load failed"));
  }, [params.id]);

  return (
    <Shell>
      <div className="mx-auto max-w-[1800px] p-5 md:p-8">
        {caseData && <TribunalStream initialCase={caseData} />}
        {!caseData && !error && <div className="court-panel p-8">Loading tribunal case</div>}
        {error && <div className="court-panel border-signal/40 p-8 text-red-100">{error}</div>}
      </div>
    </Shell>
  );
}
