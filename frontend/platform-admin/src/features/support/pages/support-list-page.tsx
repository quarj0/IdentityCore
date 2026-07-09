import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { supportConfig } from "@/features/support/mock-data";

export function SupportListPage() {
  return <AdminListPage config={supportConfig} />;
}