import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/verify/sess-12345");
}
