import { WorkflowDetailPage } from "@/features/workflows/pages/workflow-detail-page";

type PageProps = {
  params: {
    workflowId: string;
  };
};

export default async function Page({ params }: PageProps) {
  const { workflowId } = await params;
  return <WorkflowDetailPage workflowId={workflowId} />;
}
