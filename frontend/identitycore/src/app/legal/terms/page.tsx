

import { LegalPage } from "@/components/legal/legal-page";
import { legalPages } from "@/data/legal";

export default function TermsPage() {
  return <LegalPage {...legalPages.terms} />;
}