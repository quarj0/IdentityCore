import { TemplateDetailPage } from "@/features/templates/pages/template-detail-page";

type PageProps = {
  params: {
    templateId: string;
  };
};

export default function Page({ params }: PageProps) {
  return <TemplateDetailPage templateId={params.templateId} />;
}