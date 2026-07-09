import { WorkflowDetailPage } from "@/features/workflows/pages/workflow-detail-page";

type PageProps = {
  params: {
    workflowId: string;
  };
};

export default function Page({ params }: PageProps) {
  return <WorkflowDetailPage workflowId={params.workflowId} />;
}