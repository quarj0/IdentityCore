import { ReviewCaseDetailPage } from "@/features/review/pages/review-case-detail-page";

type PageProps = {
  params: {
    caseId: string;
  };
};

export default async function Page({ params }: PageProps) {
  const { caseId } = await params;
  return <ReviewCaseDetailPage caseId={caseId} />;
}
