import { ProjectDetailPage } from "@/features/projects/pages/project-detail-page";

export default function Page({ params }: { params: { id: string } }) {
  return <ProjectDetailPage id={params.id} />;
}
