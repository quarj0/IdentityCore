import Link from "next/link";
import { ArrowRight } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

interface OnboardingActionCardProps {
  title: string;
  description: string;
  href: string;
  buttonLabel: string;
}

export function OnboardingActionCard({
  title,
  description,
  href,
  buttonLabel,
}: OnboardingActionCardProps) {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription className="leading-7">{description}</CardDescription>
      </CardHeader>

      <CardContent>
        <Button asChild size="lg" className="w-full rounded-xl">
          <Link href={href}>
            {buttonLabel}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
