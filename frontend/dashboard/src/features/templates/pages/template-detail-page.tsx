import { Button } from "@identitycore/ui";
import { TemplateRequirements } from "../components/template-requirements";
import { TemplateWorkflowSteps } from "../components/template-workflow-steps";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";

export function TemplateDetailPage() {
  return (
    <ResourceDetailLayout
      backHref="/templates"
      backLabel="Back to templates"
      title="Customer onboarding template"
      description="Review requirements, providers, workflow steps, policy rules, and supported outputs."
      status="Official"
    >
      <div className="mb-6">
        <Button className="rounded-xl">Clone template</Button>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.5fr_0.5fr]">
        <TemplateRequirements />
        <TemplateWorkflowSteps />
      </div>
    </ResourceDetailLayout>
  );
}