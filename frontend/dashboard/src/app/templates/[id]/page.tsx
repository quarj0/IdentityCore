"use client";
import { useParams } from "next/navigation";
import { LiveTemplateDetail } from "@/features/templates/components/live-template-detail";

export default function Page() {
  return <LiveTemplateDetail id={String(useParams().id)} />;
}
