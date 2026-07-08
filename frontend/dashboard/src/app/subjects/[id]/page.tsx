import { GenericDetailPage } from "@/components/details/generic-detail-page";

export default function Page({ params }: { params: { id: string } }) {
  return (
    <GenericDetailPage
      backHref="/subjects"
      backLabel="Back to subjects"
      title="Subject profile"
      description={`Subject ID: ${params.id}`}
    />
  );
}
