export type TemplateStatus = "draft" | "published" | "archived";
export type TemplateCategory =
  | "Government ID"
  | "Banking KYC"
  | "Employment"
  | "Education"
  | "Healthcare"
  | "Age Verification";

export type GlobalTemplate = {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  status: TemplateStatus;
  version: string;
  countries: string[];
  requiredChecks: string[];
  usageCount: number;
  clonedByOrganizations: number;
  lastUpdatedAt: string;
  createdBy: string;
  riskLevel: "Low" | "Medium" | "High";
};

export const globalTemplates: GlobalTemplate[] = [
  {
    id: "tpl_ghana_card_standard",
    name: "Ghana Card Standard KYC",
    description:
      "Official Ghana Card verification template with document OCR, face match, liveness and manual review fallback.",
    category: "Government ID",
    status: "published",
    version: "v1.4.2",
    countries: ["Ghana"],
    requiredChecks: ["Document OCR", "Face match", "Liveness", "Expiry validation"],
    usageCount: 48210,
    clonedByOrganizations: 84,
    lastUpdatedAt: "2026-07-06",
    createdBy: "Compliance Team",
    riskLevel: "Low",
  },
  {
    id: "tpl_bank_tier_2_kyc",
    name: "Banking Tier 2 KYC",
    description:
      "Banking KYC template for regulated accounts with ID verification, address evidence and risk scoring.",
    category: "Banking KYC",
    status: "published",
    version: "v2.1.0",
    countries: ["Ghana", "Nigeria", "Kenya"],
    requiredChecks: ["Government ID", "Address evidence", "Risk scoring", "Watchlist"],
    usageCount: 67240,
    clonedByOrganizations: 132,
    lastUpdatedAt: "2026-07-02",
    createdBy: "Risk Team",
    riskLevel: "Medium",
  },
  {
    id: "tpl_student_identity",
    name: "Student Identity Verification",
    description:
      "Education-focused verification template for student onboarding, exams and campus access.",
    category: "Education",
    status: "draft",
    version: "v0.9.0",
    countries: ["Ghana", "Kenya", "Nigeria"],
    requiredChecks: ["Student ID", "Face match", "Institution email"],
    usageCount: 0,
    clonedByOrganizations: 0,
    lastUpdatedAt: "2026-07-08",
    createdBy: "Product Team",
    riskLevel: "Low",
  },
  {
    id: "tpl_healthcare_patient",
    name: "Healthcare Patient Verification",
    description:
      "Patient verification template for clinics, hospitals and telehealth identity workflows.",
    category: "Healthcare",
    status: "published",
    version: "v1.2.3",
    countries: ["Ghana", "South Africa", "Kenya"],
    requiredChecks: ["Government ID", "Consent", "Face match"],
    usageCount: 18320,
    clonedByOrganizations: 41,
    lastUpdatedAt: "2026-06-24",
    createdBy: "Compliance Team",
    riskLevel: "Medium",
  },
  {
    id: "tpl_age_restricted",
    name: "Age Restricted Access",
    description:
      "Age verification template for platforms that need proof of age without storing unnecessary identity data.",
    category: "Age Verification",
    status: "archived",
    version: "v1.0.1",
    countries: ["Ghana", "Nigeria"],
    requiredChecks: ["Document OCR", "DOB extraction", "Age policy"],
    usageCount: 8120,
    clonedByOrganizations: 19,
    lastUpdatedAt: "2026-05-30",
    createdBy: "Policy Team",
    riskLevel: "High",
  },
];

export const templateVersions = [
  {
    version: "v1.4.2",
    status: "Current",
    publishedAt: "2026-07-06",
    notes: "Improved Ghana Card expiry validation and OCR confidence thresholds.",
  },
  {
    version: "v1.4.1",
    status: "Superseded",
    publishedAt: "2026-06-18",
    notes: "Added manual review fallback for low-confidence OCR.",
  },
  {
    version: "v1.3.0",
    status: "Superseded",
    publishedAt: "2026-05-21",
    notes: "Added liveness requirement for higher-risk organizations.",
  },
];

export const templateUsageByOrganization = [
  {
    organization: "Ghana FinTrust Bank",
    environment: "Production",
    monthlyVolume: "28,420",
  },
  {
    organization: "EduVerify Africa",
    environment: "Production",
    monthlyVolume: "8,720",
  },
  {
    organization: "Civic Registry Authority",
    environment: "Staging",
    monthlyVolume: "0",
  },
];

export function getTemplateById(templateId: string) {
  return globalTemplates.find((template) => template.id === templateId);
}