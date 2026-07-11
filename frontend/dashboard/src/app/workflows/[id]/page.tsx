import {LiveWorkflowDetailPage} from "@/features/workflows/pages/live-workflow-detail-page";
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <LiveWorkflowDetailPage id={id}/>}
