import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { supportConfig } from "@/features/support/mock-data";

type SupportDetailPageProps = {
  ticketId: string;
};

export function SupportDetailPage({ ticketId }: SupportDetailPageProps) {
  return <AdminDetailPage id={ticketId} config={supportConfig} />;
}