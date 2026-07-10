import { redirect } from "next/navigation";

export default async function VerificationSessionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/verify/${id}`);
}
