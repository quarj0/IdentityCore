"use client";

import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

type InlineStatusKind = "error" | "success" | "info";

const STYLES: Record<
  InlineStatusKind,
  {
    container: string;
    icon: string;
    title: string;
  }
> = {
  error: {
    container: "border-red-200 bg-red-50 text-red-950",
    icon: "text-red-600",
    title: "There was a problem",
  },
  success: {
    container: "border-emerald-200 bg-emerald-50 text-emerald-950",
    icon: "text-emerald-600",
    title: "Success",
  },
  info: {
    container: "border-blue-200 bg-blue-50 text-blue-950",
    icon: "text-blue-600",
    title: "Information",
  },
};

export function InlineStatus({
  kind,
  message,
  title,
  durationMs = 6000,
  persist = false,
  onTimeout,
}: {
  kind: InlineStatusKind;
  message: string;
  title?: string;
  durationMs?: number;
  persist?: boolean;
  onTimeout?: () => void;
}) {
  const styles = STYLES[kind];
  const Icon = kind === "error" ? AlertCircle : kind === "success" ? CheckCircle2 : Info;
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setVisible(true);
  }, [kind, message, title]);

  useEffect(() => {
    if (persist || durationMs <= 0) {
      return;
    }

    const timeout = window.setTimeout(() => {
      setVisible(false);
      onTimeout?.();
    }, durationMs);

    return () => window.clearTimeout(timeout);
  }, [durationMs, onTimeout, persist, kind, message, title]);

  if (!visible) {
    return null;
  }

  return (
    <div className={`rounded-2xl border p-4 ${styles.container}`} role="status" aria-live="polite">
      <div className="flex gap-3">
        <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${styles.icon}`} aria-hidden="true" />
        <div className="space-y-1">
          <p className="text-sm font-semibold">{title ?? styles.title}</p>
          <p className="text-sm leading-6">{message}</p>
        </div>
      </div>
    </div>
  );
}
