"use client";

import { useEffect, useState } from "react";
import { restRequest } from "@/lib/api-client";

type Region = { box: [number, number, number, number]; reason: string; confidence: number };
type Capture = { capture_id: string; verdict: string; confidence: number | null; model_name: string | null; model_version: string | null; source_size: [number, number] | null; coordinate_space: string | null; regions: Region[] };
const reasons: Record<string, string> = { copy_move: "Duplicated region", resampling: "Resampling anomaly", text_inconsistency: "Text inconsistency", portrait_edit: "Portrait editing", template_inconsistency: "Template inconsistency" };

function CaptureEvidence({ verificationId, capture }: { verificationId: string; capture: Capture }) {
  const [image, setImage] = useState("");
  const [error, setError] = useState("");
  const [showRegions, setShowRegions] = useState(true);
  const [loading, setLoading] = useState(false);
  const [width, height] = capture.source_size || [1, 1];
  return <article className="space-y-3 rounded-xl border p-4">
    <p>Authenticity: <strong>{capture.verdict}</strong>{capture.confidence != null ? ` · confidence ${(capture.confidence * 100).toFixed(1)}%` : " · inconclusive evidence requires review"}</p>
    {capture.model_name && <p className="text-sm text-slate-600">Model: {capture.model_name} · {capture.model_version}</p>}
    {!image && <button className="rounded-lg border p-2" disabled={loading} onClick={async () => {
      setLoading(true); setError("");
      try { const data = await restRequest<{ image: string }>(`/verifications/manual-reviews/${verificationId}/authenticity/${capture.capture_id}/preview`); setImage(data.image); }
      catch { setError("The capture preview is unavailable. Refresh the evidence before making a decision."); }
      finally { setLoading(false); }
    }}>{loading ? "Loading capture..." : "View document capture"}</button>}
    {error && <p role="alert">{error}</p>}
    {image && <>
      <label className="flex gap-2"><input type="checkbox" checked={showRegions} onChange={(event) => setShowRegions(event.target.checked)} />Show suspicious regions</label>
      <svg role="img" aria-label="Document capture with suspicious region annotations" viewBox={`0 0 ${width} ${height}`} className="max-h-[640px] w-full">
        <image href={image} width={width} height={height} />
        {showRegions && capture.coordinate_space === "source_normalized" && capture.regions.map((region, index) => <rect key={index} x={region.box[0] * width} y={region.box[1] * height} width={region.box[2] * width} height={region.box[3] * height} fill="none" stroke="#dc2626" strokeWidth={Math.max(width, height) / 250}>
          <title>{reasons[region.reason] || "Suspicious region"} · confidence {(region.confidence * 100).toFixed(1)}%</title>
        </rect>)}
      </svg>
    </>}
    <ul className="list-inside list-disc text-sm">{capture.regions.map((region, index) => <li key={index}>{reasons[region.reason] || "Suspicious region"} · confidence {(region.confidence * 100).toFixed(1)}%</li>)}</ul>
  </article>;
}

export function AuthenticityEvidence({ verificationId }: { verificationId: string }) {
  const [captures, setCaptures] = useState<Capture[]>([]);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let live = true;
    restRequest<{ captures: Capture[] }>(`/verifications/manual-reviews/${verificationId}/authenticity`).then((data) => { if (live) { setCaptures(data.captures); setLoaded(true); } }).catch(() => { if (live) setError("Authenticity evidence could not be loaded or review access is unavailable."); });
    return () => { live = false; };
  }, [verificationId]);
  return <section className="space-y-3"><h2 className="text-xl font-semibold">Document authenticity evidence</h2>
    <p className="text-sm text-slate-600">Annotations support your review. Inconclusive evidence requires a human decision.</p>
    {error && <p role="alert">{error}</p>}
    {loaded && !captures.length && <p>No authenticity evidence is available.</p>}
    {captures.map((capture) => <CaptureEvidence key={capture.capture_id} verificationId={verificationId} capture={capture} />)}
  </section>;
}
