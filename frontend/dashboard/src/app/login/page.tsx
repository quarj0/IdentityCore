import { Suspense } from "react";
import { LoginPageContent } from "@/components/login/login-page";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageContent />
    </Suspense>
  );
}
