import { TemplateDetailPage } from "@/features/templates/pages/template-detail-page";

type PageProps = {
  params: Promise<{
    templateId: string;
  }>;
};

export default async function Page({ params }: PageProps) {
  const { templateId } = await params;
  return <TemplateDetailPage templateId={templateId} />;
}
