import type { ReactNode } from "react";
import { cn } from "@identitycore/ui";

interface SectionProps {
  children: ReactNode;
  className?: string;
  containerClassName?: string;
  variant?: "default" | "muted" | "dark";
}

export function Section({
  children,
  className,
  containerClassName,
  variant = "default",
}: SectionProps) {
  return (
    <section
      className={cn(
        "py-24",
        variant === "muted" && "bg-slate-50",
        variant === "dark" && "bg-slate-950 text-white",
        className,
      )}
    >
      <div className={cn("mx-auto max-w-7xl px-4 sm:px-6", containerClassName)}>
        {children}
      </div>
    </section>
  );
}
