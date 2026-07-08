import { Users } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables";

export default function SubjectsPage() {
  return (
    <ResourcePage
      title="Subjects"
      description="View people, businesses, or entities that have gone through identity workflows."
      emptyTitle="No subjects yet"
      emptyDescription="Subjects will appear after verification workflows start running."
      icon={Users}
      {...tableData.subjects}
    />
  );
}
