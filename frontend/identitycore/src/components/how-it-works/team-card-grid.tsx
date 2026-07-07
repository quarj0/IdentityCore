import { Code2, Scale, Settings2, UserRoundCheck } from "lucide-react";
import { FeatureCard } from "@/components/marketing/feature-card";

const teams = [
  {
    title: "Developers",
    description: "REST APIs, webhooks, sandbox projects, and SDKs.",
    icon: Code2,
  },
  {
    title: "Operations",
    description: "Workflow templates, policies, dashboards, and routing.",
    icon: Settings2,
  },
  {
    title: "Compliance",
    description: "Audit trails, consent records, reports, and retention.",
    icon: Scale,
  },
  {
    title: "Reviewers",
    description: "Manual review queues and explainable evidence.",
    icon: UserRoundCheck,
  },
];

export function TeamCardGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {teams.map((team) => (
        <FeatureCard key={team.title} {...team} />
      ))}
    </div>
  );
}
