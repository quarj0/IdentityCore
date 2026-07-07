import { Building, Calendar, Users } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";

const companyFacts = [
  { label: "Headquarters", value: "San Francisco, California", icon: Building },
  {
    label: "Team",
    value: "45 across engineering, operations, and risk",
    icon: Users,
  },
  { label: "Founded", value: "2024", icon: Calendar },
];

export default function CompanyPage() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingHeader activePath="/company" />

      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Company
          </h1>
          <p className="mt-4 text-lg text-muted-foreground leading-7">
            IdentityCore builds verification infrastructure that engineering
            teams can integrate quickly and compliance teams can trust under
            scrutiny.
          </p>
        </div>

        <div className="mt-14 grid gap-4 sm:grid-cols-3">
          {companyFacts.map((fact) => {
            const Icon = fact.icon;
            return (
              <Card key={fact.label} className="shadow-none">
                <CardHeader>
                  <Icon
                    className="mb-2 h-5 w-5 text-muted-foreground"
                    strokeWidth={1.75}
                  />
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {fact.label}
                  </CardTitle>
                  <CardDescription className="text-base text-foreground">
                    {fact.value}
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
