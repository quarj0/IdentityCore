import Link from "next/link";
import { Check, Fingerprint, Sparkles } from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

const plans = [
  {
    name: "Developer",
    price: "$0",
    description: "For internal prototypes, new integrations, and low-volume pilots.",
    features: [
      "100 verifications per month",
      "Hosted verification flow",
      "API and webhook access",
      "Community support",
    ],
    cta: "Start free",
  },
  {
    name: "Growth",
    price: "$149",
    description: "For teams turning verification into a production workflow.",
    features: [
      "5,000 verifications included",
      "Biometric face match and liveness",
      "Reusable review policies",
      "Email support and reporting",
    ],
    cta: "Choose growth",
    featured: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For regional scaling, white-label experiences, and advanced controls.",
    features: [
      "High-volume pricing",
      "Dedicated compliance support",
      "Custom roles and audit exports",
      "Priority onboarding",
    ],
    cta: "Talk to sales",
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen px-6 py-8 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-12">
        <header className="flex items-center justify-between rounded-3xl border border-border/70 bg-background/72 px-5 py-4 backdrop-blur-xl">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
              <Fingerprint className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-[0.18em]">IDENTITYCORE</div>
              <div className="text-xs text-muted-foreground">Pricing</div>
            </div>
          </Link>
          <Button asChild variant="outline" size="sm">
            <a href="http://localhost:3000">Open dashboard</a>
          </Button>
        </header>

        <section className="space-y-5 text-center">
          <Badge variant="info" className="px-4 py-1.5">
            <Sparkles className="h-3.5 w-3.5" />
            Transparent product stages
          </Badge>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Pricing built around operational maturity.
          </h1>
          <p className="mx-auto max-w-2xl text-lg leading-8 text-muted-foreground">
            Start light, scale into policy-driven review, and move to enterprise controls when verification becomes a core trust surface.
          </p>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={plan.featured ? "relative border-primary/40 bg-linear-to-b from-primary/[0.06] via-background to-background" : ""}
            >
              <CardHeader>
                {plan.featured ? (
                  <Badge className="mb-3 w-fit" variant="default">
                    Recommended
                  </Badge>
                ) : null}
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <div className="flex items-end gap-2">
                  <div className="text-4xl font-semibold tracking-tight">{plan.price}</div>
                  {plan.price !== "Custom" ? (
                    <div className="pb-1 text-sm text-muted-foreground">/month</div>
                  ) : null}
                </div>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex gap-3 text-sm text-muted-foreground">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span>{feature}</span>
                  </div>
                ))}
              </CardContent>
              <CardFooter>
                <Button className="w-full" variant={plan.featured ? "default" : "outline"}>
                  {plan.cta}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </section>
      </div>
    </div>
  );
}
