import { redirect } from "next/navigation";

export default function OnboardingVerifyEmailPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const query = new URLSearchParams();

  for (const [key, value] of Object.entries(searchParams)) {
    if (Array.isArray(value)) {
      value.forEach((item) => query.append(key, item));
    } else if (value !== undefined) {
      query.append(key, value);
    }
  }

  const queryString = query.toString();
  redirect(`/verify-email${queryString ? `?${queryString}` : ""}`);
}
