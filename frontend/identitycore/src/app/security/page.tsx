import { Award, Lock, Workflow } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";

const securityAreas = [
  {
    title: "Data protection",
    description:
      "Documents, biometric media, and reviewer notes are encrypted in transit and at rest with strict access boundaries.",
    icon: Lock,
  },
  {
    title: "Operational controls",
    description:
      "Every reviewer action, approval, and escalation is logged with attribution for compliance and incident response.",
    icon: Workflow,
  },
  {
    title: "Governance alignment",
    description:
      "Built to support vendor assessments, retention policies, and least-privilege access patterns required in regulated industries.",
    icon: Award,
  },
];

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingHeader activePath="/security" />

      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Security
          </h1>
          <p className="mt-4 text-lg text-muted-foreground leading-7">
            Identity verification handles sensitive personal data. Our platform
            is designed with security and compliance as foundational
            requirements, not add-ons.
          </p>
        </div>

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {securityAreas.map((area) => {
            const Icon = area.icon;
            return (
              <Card key={area.title} className="shadow-none">
                <CardHeader>
                  <Icon
                    className="mb-3 h-5 w-5 text-muted-foreground"
                    strokeWidth={1.75}
                  />
                  <CardTitle className="text-base">{area.title}</CardTitle>
                  <CardDescription className="leading-6">
                    {area.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
