import { KeyRound } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables";

export default function ApiKeysPage() {
  return (
    <ResourcePage
      title="API keys"
      description="Manage sandbox and production credentials for your workspace."
      actionLabel="Create API key"
      emptyTitle="No API keys yet"
      emptyDescription="Create an API key to start testing IdentityCore."
      icon={KeyRound}
      {...tableData.apiKeys}
    />
  );
}
