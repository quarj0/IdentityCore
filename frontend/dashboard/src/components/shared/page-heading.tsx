import type { ReactNode } from "react";

interface PageHeadingProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function PageHeading({ title, description, action }: PageHeadingProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          {title}
        </h1>

        {description ? (
          <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600">
            {description}
          </p>
        ) : null}
      </div>

      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
