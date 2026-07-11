import { LiveWorkflowsPage } from "@/features/workflows/pages/live-workflows-page";

export default async function WorkflowsPage({ searchParams }: { searchParams: Promise<{ template?: string }> }) {
  const { template = "" } = await searchParams;
  return <LiveWorkflowsPage templateSlug={template} />;
}
