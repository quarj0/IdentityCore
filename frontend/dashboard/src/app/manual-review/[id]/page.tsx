"use client";
import { useParams } from "next/navigation";
import { LiveVerificationDetail } from "@/features/verifications/components/live-verification-detail";

export default function Page() {
  return <LiveVerificationDetail id={String(useParams().id)} review />;
}
