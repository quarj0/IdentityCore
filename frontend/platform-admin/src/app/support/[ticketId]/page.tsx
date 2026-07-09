import { SupportDetailPage } from "@/features/support/pages/support-detail-page";

type PageProps = { params: { ticketId: string } };

export default function Page({ params }: PageProps) {
  return <SupportDetailPage ticketId={params.ticketId} />;
}