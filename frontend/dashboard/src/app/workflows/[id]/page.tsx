import Link from "next/link";
import { Button } from "@identitycore/ui";
import { WorkflowBuilderCanvas } from "@/features/workflows/components/workflow-builder-canvas";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";

export default function Page() {
  return (
    <ResourceDetailLayout
      backHref="/workflows"
      backLabel="Back to workflows"
      title="Customer onboarding workflow"
      description="Manage workflow configuration, versions, history, and publishing."
      status="Draft"
    >
      <div className="mb-6 flex gap-3">
        <Button asChild className="rounded-xl">
          <Link href="/workflows/demo/builder">Open builder</Link>
        </Button>
        <Button asChild variant="outline" className="rounded-xl">
          <Link href="/workflows/demo/history">View history</Link>
        </Button>
      </div>

      <WorkflowBuilderCanvas />
    </ResourceDetailLayout>
  );
}
