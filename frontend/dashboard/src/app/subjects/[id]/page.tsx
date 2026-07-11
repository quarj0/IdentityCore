"use client";
import {use} from "react"; import {LiveResourceDetail} from "@/features/operations/live-resource-detail"; import {dashboardApi} from "@/lib/dashboard-api";
export default function Page({params}:{params:Promise<{id:string}>}){const {id}=use(params);return <LiveResourceDetail title="Subject profile" description={`Subject ID: ${id}`} load={()=>dashboardApi.subject(id)}/>}
