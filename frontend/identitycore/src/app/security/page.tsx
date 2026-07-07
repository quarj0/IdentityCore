import Link from "next/link";
import { Award, Fingerprint, Lock, ShieldCheck, Workflow } from "lucide-react";
import {
  Badge,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

const securityAreas = [
  {
    title: "Protected data handling",
    description:
      "Uploaded documents, biometric media, and reviewer notes follow encrypted transport and storage boundaries throughout the flow.",
    icon: Lock,
  },
  {
    title: "Operational control",
    description:
      "Reviewer actions, approvals, and escalations remain attributable so compliance teams can understand exactly what happened and why.",
    icon: Workflow,
  },
  {
    title: "Standards alignment",
    description:
      "The platform is shaped for serious governance expectations including vendor review, retention controls, and least-privilege access patterns.",
    icon: Award,
  },
];

export default function SecurityPage() {
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
              <div className="text-xs text-muted-foreground">Security</div>
            </div>
          </Link>
          <Badge variant="info">
            <ShieldCheck className="h-3.5 w-3.5" />
            Trust posture
          </Badge>
        </header>

        <section className="space-y-5">
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Security needs to feel operational, not decorative.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
            Verification products carry sensitive identity evidence. We design the system so storage, review, and decision-making all support that reality.
          </p>
        </section>

        <section className="grid gap-6 md:grid-cols-3">
          {securityAreas.map((area) => {
            const Icon = area.icon;
            return (
              <Card key={area.title}>
                <CardHeader className="space-y-4">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="space-y-2">
                    <CardTitle>{area.title}</CardTitle>
                    <CardDescription>{area.description}</CardDescription>
                  </div>
                </CardHeader>
              </Card>
            );
          })}
        </section>
      </div>
    </div>
  );
}
