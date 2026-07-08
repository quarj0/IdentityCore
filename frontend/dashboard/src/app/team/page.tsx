import { Users } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables";

export default function TeamPage() {
  return (
    <ResourcePage
      title="Team"
      description="Manage workspace members, roles, and permissions."
      actionLabel="Invite member"
      emptyTitle="No team members yet"
      emptyDescription="Invite team members to collaborate on workflows and reviews."
      icon={Users}
      {...tableData.team}
    />
  );
}
