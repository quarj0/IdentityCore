import { Card, CardContent } from "@identitycore/ui";

interface MetricCardProps {
  label: string;
  value: string;
  description: string;
}

export function MetricCard({ label, value, description }: MetricCardProps) {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardContent className="p-6">
        <p className="text-sm text-slate-600">{label}</p>
        <p className="mt-3 text-3xl font-semibold tracking-tight">{value}</p>
        <p className="mt-2 text-sm text-slate-500">{description}</p>
      </CardContent>
    </Card>
  );
}
