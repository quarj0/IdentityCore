import { FileCheck2 } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables";

export default function VerificationRequestsPage() {
  return (
    <ResourcePage
      title="Verification requests"
      description="Track hosted verification links and workflow sessions."
      actionLabel="Create request"
      emptyTitle="No verification requests yet"
      emptyDescription="Create a request to invite someone into a hosted identity workflow."
      icon={FileCheck2}
      {...tableData.requests}
    />
  );
}
