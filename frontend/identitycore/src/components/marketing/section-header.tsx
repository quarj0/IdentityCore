import type { ReactNode } from "react";

interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  centered?: boolean;
  children?: ReactNode;
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  centered,
  children,
}: SectionHeaderProps) {
  return (
    <div className={centered ? "mx-auto max-w-3xl text-center" : "max-w-3xl"}>
      {eyebrow ? (
        <p className="text-sm font-medium text-blue-600">{eyebrow}</p>
      ) : null}

      <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
        {title}
      </h2>

      {description ? (
        <p className="mt-5 text-lg leading-8 text-muted-foreground">
          {description}
        </p>
      ) : null}

      {children}
    </div>
  );
}
