import { Building2 } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <NoBackendModulePage
      title="Project"
      description={`Project ID: ${id}`}
      emptyTitle="Project detail API is not available yet"
      emptyDescription="Project data has been removed from the UI until it can be backed by real tenant APIs."
      icon={Building2}
    />
  );
}
