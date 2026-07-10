import Link from "next/link";
import { AlertTriangle, CheckCircle2, Clock3 } from "lucide-react";
import { Badge, Button, Card, CardContent } from "@identitycore/ui";

export function SessionStatePage({
  title,
  description,
  badge,
  icon,
  primaryHref,
  primaryLabel,
}: {
  title: string;
  description: string;
  badge: string;
  icon: "complete" | "error" | "expired";
  primaryHref: string;
  primaryLabel: string;
}) {
  const Icon = icon === "complete" ? CheckCircle2 : icon === "expired" ? Clock3 : AlertTriangle;
  return (
    <Card className="mx-auto max-w-xl rounded-3xl border-slate-200 shadow-sm">
      <CardContent className="flex min-h-96 flex-col items-center justify-center p-8 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><Icon className="h-7 w-7" /></div>
        <Badge variant="secondary" className="mt-5">{badge}</Badge>
        <h1 className="mt-5 text-2xl font-semibold">{title}</h1>
        <p className="mt-3 max-w-md text-sm leading-7 text-slate-600">{description}</p>
        <Button asChild className="mt-7"><Link href={primaryHref}>{primaryLabel}</Link></Button>
      </CardContent>
    </Card>
  );
}
