import { AdminDetailPage } from "@/features/users/pages/admin-detail-page";

type PageProps = {
  params: {
    userId: string;
  };
};

export default function Page({ params }: PageProps) {
  return <AdminDetailPage userId={params.userId} />;
}
