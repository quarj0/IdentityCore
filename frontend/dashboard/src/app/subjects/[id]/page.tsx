import { Users } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <NoBackendModulePage
      title="Subject profile"
      description={`Subject ID: ${id}`}
      emptyTitle="Subject detail API is not available yet"
      emptyDescription="Use the live Subjects list to review tenant-scoped verification subjects."
      icon={Users}
    />
  );
}
