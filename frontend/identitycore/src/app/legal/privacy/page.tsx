import { LegalPage } from "@/components/legal/legal-page";
import { legalPages } from "@/data/legal";

export default function PrivacyPage() {
  return <LegalPage {...legalPages.privacy} />;
}
