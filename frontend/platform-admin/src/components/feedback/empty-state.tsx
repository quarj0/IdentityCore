import type { ReactNode } from "react";
import { Inbox } from "lucide-react";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 bg-white/2 p-8 text-center">
      <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-white/5 text-slate-400">
        <Inbox className="size-6" aria-hidden="true" />
      </div>

      <h3 className="mt-4 text-sm font-semibold text-white">{title}</h3>
      <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-400">
        {description}
      </p>

      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
