"use client";
import {use} from "react"; import {LiveResourceDetail} from "@/features/operations/live-resource-detail"; import {dashboardApi} from "@/lib/dashboard-api";
export default function Page({params}:{params:Promise<{id:string}>}){const {id}=use(params);return <LiveResourceDetail title="Project" description={`Project ID: ${id}`} load={()=>dashboardApi.project(id) as Promise<unknown> as Promise<Record<string,unknown>>}/>}
