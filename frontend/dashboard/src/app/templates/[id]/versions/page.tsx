import { FileText } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function Page() {
  return (
    <NoBackendModulePage
      title="Template versions"
      description="Template versions are represented by policy records in the live Templates list."
      emptyTitle="Dedicated version history is not exposed yet"
      emptyDescription="Use the Templates list and detail pages to inspect, clone, activate, and archive real policy versions."
      icon={FileText}
    />
  );
}
