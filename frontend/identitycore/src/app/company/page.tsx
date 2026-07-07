import Link from "next/link";
import { Building, Calendar, Fingerprint, Users } from "lucide-react";
import {
  Badge,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

const companyFacts = [
  { label: "Headquarters", value: "San Francisco, California", icon: Building },
  { label: "Team footprint", value: "45 operators, engineers, and risk specialists", icon: Users },
  { label: "Founded", value: "2024", icon: Calendar },
];

export default function CompanyPage() {
  return (
    <div className="min-h-screen px-6 py-8 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-12">
        <header className="flex items-center justify-between rounded-3xl border border-border/70 bg-background/72 px-5 py-4 backdrop-blur-xl">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
              <Fingerprint className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-[0.18em]">IDENTITYCORE</div>
              <div className="text-xs text-muted-foreground">Company</div>
            </div>
          </Link>
          <Badge variant="secondary">People behind the platform</Badge>
        </header>

        <section className="grid gap-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-start">
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
              We’re building verification infrastructure that teams can trust under pressure.
            </h1>
            <p className="text-lg leading-8 text-muted-foreground">
              IdentityCore exists to make identity operations clearer for engineers, safer for compliance teams, and easier for end users moving through high-trust flows.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            {companyFacts.map((fact) => {
              const Icon = fact.icon;
              return (
                <Card key={fact.label}>
                  <CardHeader className="space-y-4">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="space-y-1">
                      <CardTitle className="text-base">{fact.label}</CardTitle>
                      <CardDescription>{fact.value}</CardDescription>
                    </div>
                  </CardHeader>
                </Card>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
