import { AdminDetailPage } from "@/features/users/pages/admin-detail-page";

type PageProps = {
  params: Promise<{
    userId: string;
  }>;
};

export default async function Page({ params }: PageProps) {
  const { userId } = await params;
  return <AdminDetailPage userId={userId} />;
}
