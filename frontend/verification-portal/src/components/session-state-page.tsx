import Link from "next/link";
import { AlertTriangle, CheckCircle2, Clock3 } from "lucide-react";
import { Badge, BrandMark, Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";

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
  icon: "complete" | "expired" | "error";
  primaryHref: string;
  primaryLabel: string;
}) {
  const Icon = icon === "complete" ? CheckCircle2 : icon === "expired" ? Clock3 : AlertTriangle;
  const variant = icon === "complete" ? "success" : icon === "expired" ? "warning" : "destructive";

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <Card className="w-full max-w-xl shadow-sm">
        <CardHeader className="space-y-6 text-center">
          <div className="mx-auto">
            <BrandMark subtitle="Secure verification session" size="md" />
          </div>
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Icon className="h-8 w-8" />
          </div>
          <div className="space-y-3">
            <Badge variant={variant}>{badge}</Badge>
            <CardTitle className="text-2xl">{title}</CardTitle>
            <CardDescription className="text-sm leading-6">{description}</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex justify-center">
          <Button asChild>
            <Link href={primaryHref}>{primaryLabel}</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
