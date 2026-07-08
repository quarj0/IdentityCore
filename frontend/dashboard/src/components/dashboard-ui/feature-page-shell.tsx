import type { ReactNode } from "react";
import { PageHeading } from "@/components/shared/page-heading";

interface FeaturePageShellProps {
  title: string;
  description: string;
  action?: ReactNode;
  children: ReactNode;
}

export function FeaturePageShell({
  title,
  description,
  action,
  children,
}: FeaturePageShellProps) {
  return (
    <div className="space-y-8">
      <PageHeading title={title} description={description} action={action} />
      {children}
    </div>
  );
}
