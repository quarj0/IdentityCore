import { LiveProjectDetailPage } from "@/features/projects/pages/live-project-detail-page";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <LiveProjectDetailPage id={id} settings />;
}
