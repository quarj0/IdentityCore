import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

interface OnboardingTierCardProps {
  title: string;
  description: string;
  ctaHref: string;
  ctaLabel: string;
  summary: string;
  badge?: string;
  features?: string[];
}

export function OnboardingTierCard({
  title,
  description,
  ctaHref,
  ctaLabel,
  summary,
  badge,
  features = [],
}: OnboardingTierCardProps) {
  return (
    <Card className="h-fit rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
      <CardHeader>
        {badge ? (
          <Badge variant="secondary" className="mb-2 w-fit rounded-full">
            {badge}
          </Badge>
        ) : null}
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm font-semibold">{summary}</p>
        </div>

        {features.length > 0 ? (
          <div className="space-y-3">
            {features.map((feature) => (
              <div key={feature} className="flex gap-3 text-sm text-muted-foreground">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
                {feature}
              </div>
            ))}
          </div>
        ) : null}

        <Button asChild size="lg" className="w-full rounded-xl">
          <Link href={ctaHref}>
            {ctaLabel}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
