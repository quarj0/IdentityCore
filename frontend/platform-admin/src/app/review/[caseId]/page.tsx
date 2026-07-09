import { ReviewCaseDetailPage } from "@/features/review/pages/review-case-detail-page";

type PageProps = {
  params: {
    caseId: string;
  };
};

export default function Page({ params }: PageProps) {
  return <ReviewCaseDetailPage caseId={params.caseId} />;
}