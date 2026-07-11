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
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";

const plans = [
  {
    name: "Trial",
    price: "Free",
    description: "Explore IdentityCore with sandbox workflows.",
    features: [
      "Sandbox workspace",
      "Sandbox verification responses",
      "Workflow templates",
      "Developer documentation",
    ],
    cta: "Start trial",
    href: "/register",
  },
  {
    name: "Growth",
    price: "Usage-based",
    description: "For teams launching hosted verification and API workflows.",
    features: [
      "Production workflows",
      "Hosted verification links",
      "REST APIs and webhooks",
      "Basic policy builder",
      "Standard support",
    ],
    cta: "Create workspace",
    href: "/register",
  },
  {
    name: "Business",
    price: "Custom",
    description: "For organizations with higher volume and governance needs.",
    features: [
      "Advanced policies",
      "Manual review workflows",
      "Provider routing",
      "Audit exports",
      "Higher limits",
    ],
    cta: "Talk to us",
    href: "/company",
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For regulated, private, or government-style deployments.",
    features: [
      "Dedicated deployment options",
      "Custom provider integrations",
      "Private cloud/on-premise planning",
      "Custom SLAs",
      "Priority support",
    ],
    cta: "Book demo",
    href: "/company",
  },
];

const enterpriseItems = [
  "Dedicated infrastructure planning",
  "Provider integration support",
  "Custom limits and SLAs",
  "Implementation and maintenance agreements",
];

export function PricingPageContent() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/pricing" />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-140 bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto max-w-7xl px-6 py-24 lg:py-32">
            <Badge variant="secondary" className="rounded-full px-3 py-1">
              Pricing
            </Badge>

            <h1 className="mt-6 max-w-5xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
              Pricing for identity workflows at every stage.
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
              Start with sandbox workflows, launch production verification, and
              grow into advanced provider routing, governance, and dedicated
              deployment options.
            </p>
          </div>
        </section>

        <section className="pb-24">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 lg:grid-cols-4">
            {plans.map((plan) => (
              <Card
                key={plan.name}
                className="flex rounded-3xl border-slate-200 bg-white p-2 shadow-sm"
              >
                <div className="flex w-full flex-col">
                  <CardHeader>
                    <CardTitle>{plan.name}</CardTitle>
                    <p className="pt-4 text-3xl font-semibold tracking-tight">
                      {plan.price}
                    </p>
                    <CardDescription className="leading-7">
                      {plan.description}
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="flex flex-1 flex-col px-6 pb-6">
                    <div className="space-y-3">
                      {plan.features.map((feature) => (
                        <div
                          key={feature}
                          className="flex gap-3 text-sm text-muted-foreground"
                        >
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
                          {feature}
                        </div>
                      ))}
                    </div>

                    <Button asChild className="mt-8 rounded-xl">
                      <Link href={plan.href}>
                        {plan.cta}
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    </Button>
                  </CardContent>
                </div>
              </Card>
            ))}
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                Enterprise deployments
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Pricing changes when infrastructure ownership changes.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                For government, enterprise, and regulated customers,
                IdentityCore can be licensed with support, implementation, and
                dedicated deployment planning.
              </p>
            </div>

            <div className="grid gap-3">
              {enterpriseItems.map((item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-white/10 bg-white/4 p-5 text-sm font-medium text-slate-100"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-4xl px-6 text-center">
            <h2 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Start in sandbox. Scale into infrastructure.
            </h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
              Create your workspace, test workflows, and decide when you are
              ready for production usage.
            </p>
            <div className="mt-10 flex justify-center gap-3">
              <Button asChild size="lg" className="rounded-xl">
                <Link href="/register">
                  Create workspace
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="rounded-xl"
              >
                <Link href="/platform">Explore platform</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
