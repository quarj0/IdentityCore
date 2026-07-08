import { ShieldCheck } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables";

export default function ManualReviewPage() {
  return (
    <ResourcePage
      title="Manual review"
      description="Review cases that require human decisioning or additional evidence."
      emptyTitle="No cases waiting for review"
      emptyDescription="Cases appear here when policies route them to manual review."
      icon={ShieldCheck}
      {...tableData.reviews}
    />
  );
}
