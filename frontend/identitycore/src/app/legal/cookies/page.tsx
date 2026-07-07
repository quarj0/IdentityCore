import { LegalPage } from "@/components/legal/legal-page";
import { legalPages } from "@/data/legal";

export default function CookiesPage() {
  return <LegalPage {...legalPages.cookies} />;
}