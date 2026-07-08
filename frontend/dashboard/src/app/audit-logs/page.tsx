import { ScrollText } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables";

export default function AuditLogsPage() {
  return (
    <ResourcePage
      title="Audit logs"
      description="Review sensitive actions and system events in your workspace."
      emptyTitle="No audit logs yet"
      emptyDescription="Audit logs will appear as your workspace is used."
      icon={ScrollText}
      {...tableData.auditLogs}
    />
  );
}
