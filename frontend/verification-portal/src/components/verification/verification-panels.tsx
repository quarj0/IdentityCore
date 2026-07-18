"use client";

import { useEffect, useState, type ReactNode } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  FileCheck2,
  Loader2,
  RotateCcw,
  ShieldAlert,
  XCircle,
} from "lucide-react";

import { Button, Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

export function StepCard({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <Card className="overflow-hidden rounded-[2rem] border-slate-200 bg-white shadow-xl shadow-slate-200/40">
      <CardHeader className="border-b border-slate-100 px-5 py-6 sm:px-8 sm:py-7">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-600">{eyebrow}</p>
        <CardTitle className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
          {title}
        </CardTitle>
        <p className="max-w-2xl text-sm leading-6 text-slate-500">{description}</p>
      </CardHeader>
      <CardContent className="space-y-5 px-5 py-6 sm:px-8 sm:py-8">{children}</CardContent>
    </Card>
  );
}

export function EvidenceReview({
  file,
  onRetake,
}: {
  file: File;
  onRetake: () => void;
}) {
  const [url, setUrl] = useState("");
  const [previewFailed, setPreviewFailed] = useState(false);

  useEffect(() => {
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    setPreviewFailed(false);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-950">
      {previewFailed ? (
        <div className="flex min-h-72 flex-col items-center justify-center px-6 text-center text-amber-200">
          <AlertTriangle className="h-7 w-7" aria-hidden="true" />
          <p className="mt-3 text-sm">This image cannot be previewed. Retake or choose another file.</p>
        </div>
      ) : (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img
          src={url}
          onError={() => setPreviewFailed(true)}
          alt="Captured evidence preview"
          className="max-h-[32rem] min-h-72 w-full object-contain"
        />
      )}
      <div className="flex items-center justify-between gap-4 border-t border-white/10 px-4 py-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium text-white">{file.name}</p>
          <p className="mt-0.5 text-xs text-slate-400">{formatBytes(file.size)}</p>
        </div>
        <Button type="button" size="sm" variant="outline" onClick={onRetake} className="border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white">
          <RotateCcw className="h-3.5 w-3.5" />
          Retake
        </Button>
      </div>
    </div>
  );
}

export function ProcessingPanel({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <div className="rounded-3xl border border-blue-100 bg-blue-50/60 p-5">
      <div className="flex gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
        </span>
        <div>
          <p className="text-sm font-semibold text-blue-950">{title}</p>
          <p className="mt-1 text-xs leading-5 text-blue-900/65">Keep this page open. This usually takes less than a minute.</p>
        </div>
      </div>
      <div className="mt-5 grid gap-2 sm:grid-cols-2">
        {items.map((item) => (
          <div key={item} className="flex items-center gap-2 rounded-2xl bg-white/80 px-3 py-2.5 text-xs font-medium text-slate-600">
            <FileCheck2 className="h-4 w-4 text-blue-600" aria-hidden="true" />
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

export function TerminalPanel({
  state,
  message,
  onFinish,
}: {
  state: "verified" | "review" | "failed" | "expired" | "cancelled";
  message: string;
  onFinish?: () => void;
}) {
  const config = {
    verified: {
      icon: CheckCircle2,
      title: "Verification complete",
      detail: "Your identity evidence was verified successfully.",
      tone: "border-emerald-100 bg-emerald-50 text-emerald-800",
    },
    review: {
      icon: Clock3,
      title: "Submitted for review",
      detail: "Your evidence was received securely. The requesting organization will review it.",
      tone: "border-amber-100 bg-amber-50 text-amber-800",
    },
    failed: {
      icon: XCircle,
      title: "Verification needs attention",
      detail: "We could not complete this verification with the submitted evidence.",
      tone: "border-red-100 bg-red-50 text-red-800",
    },
    expired: {
      icon: ShieldAlert,
      title: "This session has expired",
      detail: "For your security, verification links are available only for a limited time.",
      tone: "border-slate-200 bg-slate-50 text-slate-700",
    },
    cancelled: {
      icon: ShieldAlert,
      title: "Verification cancelled",
      detail: "The requesting organization cancelled this verification session.",
      tone: "border-slate-200 bg-slate-50 text-slate-700",
    },
  }[state];
  const Icon = config.icon;

  return (
    <div className={`rounded-3xl border p-6 ${config.tone}`}>
      <Icon className="h-9 w-9" aria-hidden="true" />
      <h2 className="mt-4 text-xl font-semibold">{config.title}</h2>
      <p className="mt-2 text-sm leading-6">{message || config.detail}</p>
      {onFinish ? (
        <Button type="button" onClick={onFinish} className="mt-6">
          Finish and return
        </Button>
      ) : null}
    </div>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
