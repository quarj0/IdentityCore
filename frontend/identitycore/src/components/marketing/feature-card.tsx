import type { LucideIcon } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";

interface FeatureCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export function FeatureCard({
  title,
  description,
  icon: Icon,
}: FeatureCardProps) {
  return (
    <Card className="group rounded-3xl border-slate-200 bg-white p-2 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl">
      <CardHeader className="p-6">
        <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-50 ring-1 ring-slate-200 group-hover:bg-blue-50 group-hover:text-blue-700">
          <Icon className="h-5 w-5" strokeWidth={1.75} aria-hidden="true" />
        </div>

        <CardTitle>{title}</CardTitle>
        <CardDescription className="pt-2 leading-7">
          {description}
        </CardDescription>
      </CardHeader>
    </Card>
  );
}
