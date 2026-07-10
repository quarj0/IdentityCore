import type { ReactNode } from "react";

interface CapturePanelProps {
  title: string;
  description: string;
  children: ReactNode;
}

export function CapturePanel({
  title,
  description,
  children,
}: CapturePanelProps) {
  return (
    <section className="rounded-4xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
        {title}
      </h1>

      <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600">
        {description}
      </p>

      <div className="mt-6">{children}</div>
    </section>
  );
}
