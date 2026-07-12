import { SupportDetailPage } from "@/features/support/pages/support-detail-page";

type PageProps = { params: { ticketId: string } };

export default async function Page({ params }: PageProps) {
  const { ticketId } = await params;
  return <SupportDetailPage ticketId={ticketId} />;
}
