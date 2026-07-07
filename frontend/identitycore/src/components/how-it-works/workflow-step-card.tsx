import type { LucideIcon } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";

interface WorkflowStepCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  index: number;
}

export function WorkflowStepCard({
  title,
  description,
  icon: Icon,
  index,
}: WorkflowStepCardProps) {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <Icon className="h-5 w-5" />
        </div>
        <p className="text-xs font-medium text-muted-foreground">
          Step {index + 1}
        </p>
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription className="leading-7">{description}</CardDescription>
      </CardHeader>
    </Card>
  );
}
