"use client";
import {use} from "react"; import {LiveResourceDetail} from "@/features/operations/live-resource-detail"; import {dashboardApi} from "@/lib/dashboard-api";
export default function Page({params}:{params:Promise<{id:string}>}){const {id}=use(params);return <LiveResourceDetail title="Workflow versions" description="Immutable publication history" load={()=>dashboardApi.workflowVersions(id) as Promise<unknown> as Promise<Record<string,unknown>>}/>}
