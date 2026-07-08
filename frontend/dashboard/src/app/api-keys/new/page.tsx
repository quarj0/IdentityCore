import { ApiKeyForm } from "@/components/forms/api-key-form";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Create API key"
        description="Create a sandbox or production API key for server-side integrations."
      />
      <ApiKeyForm />
    </div>
  );
}
