import { FileText } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables";

export default function TemplatesPage() {
  return (
    <ResourcePage
      title="Templates"
      description="Clone official workflow templates into your workspace."
      actionLabel="Browse templates"
      emptyTitle="No templates cloned yet"
      emptyDescription="Clone a template to start building faster."
      icon={FileText}
      {...tableData.templates}
    />
  );
}