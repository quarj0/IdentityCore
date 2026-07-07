import type { LucideIcon } from "lucide-react";
import {
  Building2,
  GraduationCap,
  HeartPulse,
  Landmark,
  ShieldCheck,
  Users,
} from "lucide-react";

export interface WorkflowTemplate {
  slug: string;
  title: string;
  category: string;
  description: string;
  icon: LucideIcon;
  tags: string[];
  audience: string;
  outcome: string;
  turnaround: string;
  highlights: string[];
  required: string[];
  steps: string[];
  providers: string[];
  policies: string[];
  launchChecklist: string[];
  whyItMatters: string[];
}

export const workflowTemplates: WorkflowTemplate[] = [
  {
    slug: "customer-onboarding",
    title: "Customer onboarding",
    category: "Financial services",
    description:
      "Verify identity, collect consent, run document checks, and route risky cases to review.",
    icon: Landmark,
    tags: ["KYC", "Face match", "Risk"],
    audience: "Banks, fintechs, lenders, wallets, and investment platforms.",
    outcome:
      "Approve legitimate customers faster while routing suspicious onboarding attempts to manual review.",
    turnaround: "Typical launch: 1 to 2 weeks with hosted workflows or API onboarding.",
    highlights: [
      "Built for KYC and regulated account opening journeys",
      "Supports document capture, selfie, liveness, and risk scoring",
      "Keeps audit evidence for compliance and dispute resolution",
    ],
    required: [
      "National ID, passport, or driver's license",
      "Selfie capture",
      "Liveness check",
      "Email address",
      "Consent confirmation",
    ],
    steps: [
      "Consent",
      "Document capture",
      "OCR extraction",
      "Selfie capture",
      "Liveness check",
      "Face match",
      "Risk decision",
      "Webhook result",
    ],
    providers: ["IdentityCore OCR", "Face match", "Liveness", "Risk engine"],
    policies: [
      "Manual review when face match is below threshold",
      "Reject expired documents",
      "Require liveness for production workflows",
    ],
    launchChecklist: [
      "Choose supported identity documents by market",
      "Set risk thresholds and review escalation rules",
      "Define webhook destination for onboarding decisions",
      "Configure retention for evidence and consent records",
    ],
    whyItMatters: [
      "Reduces drop-off during account creation",
      "Creates a reusable onboarding flow across products",
      "Improves compliance readiness for audits",
    ],
  },
  {
    slug: "student-enrollment",
    title: "Student enrollment",
    category: "Education",
    description:
      "Confirm student identity during admissions, online learning, examinations, and certificate workflows.",
    icon: GraduationCap,
    tags: ["ID check", "Selfie", "Liveness"],
    audience:
      "Universities, edtech products, certification providers, and exam platforms.",
    outcome:
      "Ensure the enrolled or examined student is the right person without slowing admissions or learning access.",
    turnaround: "Typical launch: a few days for pilot enrollment and exam verification.",
    highlights: [
      "Supports remote admissions and online assessment programs",
      "Works for enrollment, exam sitting, and certificate release",
      "Flexible enough for lighter checks during low-risk flows",
    ],
    required: [
      "National ID or passport",
      "Student email address",
      "Selfie capture",
      "Optional liveness check",
    ],
    steps: [
      "Consent",
      "Student details",
      "Document capture",
      "OCR extraction",
      "Selfie capture",
      "Face match",
      "Decision",
    ],
    providers: ["IdentityCore OCR", "Face match", "Policy engine"],
    policies: [
      "Allow national ID or passport",
      "Manual review for low OCR confidence",
      "Expire unfinished sessions after configured time",
    ],
    launchChecklist: [
      "Map the student lifecycle stage that requires identity proof",
      "Choose when selfie-only versus liveness-assisted checks apply",
      "Define fallback handling for minors or missing ID documents",
      "Connect pass or fail results into admissions or LMS systems",
    ],
    whyItMatters: [
      "Protects remote learning and examination integrity",
      "Reduces impersonation during certificate workflows",
      "Gives operations teams one consistent review queue",
    ],
  },
  {
    slug: "employee-verification",
    title: "Employee verification",
    category: "HR",
    description:
      "Verify employees, contractors, and temporary workers before granting access or onboarding.",
    icon: Users,
    tags: ["Documents", "Review", "Audit"],
    audience:
      "HR platforms, internal IT teams, BPOs, staffing firms, and enterprise onboarding teams.",
    outcome:
      "Establish workforce identity before account creation, system access, or equipment provisioning.",
    turnaround:
      "Typical launch: 1 week when connected to HRIS and access request processes.",
    highlights: [
      "Useful for employees, contractors, interns, and temporary workers",
      "Can sit before IT provisioning or physical access activation",
      "Produces clear audit records for internal controls",
    ],
    required: ["Government ID", "Selfie", "Employment reference ID"],
    steps: ["Consent", "Document", "Selfie", "Face match", "Review", "Audit"],
    providers: ["IdentityCore OCR", "Face match", "Manual review"],
    policies: [
      "Require reviewer approval for contractors",
      "Keep audit evidence based on retention policy",
    ],
    launchChecklist: [
      "Define workforce categories and approval requirements",
      "Decide who can override mismatches or exceptions",
      "Connect outcomes into HRIS, IAM, or service desk tooling",
      "Set retention windows for employee identity evidence",
    ],
    whyItMatters: [
      "Prevents mistaken or fraudulent account provisioning",
      "Creates a repeatable process across workforce types",
      "Supports internal audit and access governance reviews",
    ],
  },
  {
    slug: "patient-registration",
    title: "Patient registration",
    category: "Healthcare",
    description:
      "Verify patient identity for registration, telemedicine, insurance, and controlled service access.",
    icon: HeartPulse,
    tags: ["Consent", "Records", "Risk"],
    audience:
      "Hospitals, clinics, telehealth platforms, insurers, and digital health services.",
    outcome:
      "Reduce duplicate or misidentified patient records while keeping access simple for legitimate patients.",
    turnaround:
      "Typical launch: 1 to 2 weeks depending on clinical and consent requirements.",
    highlights: [
      "Supports remote registration and controlled service access",
      "Centers consent collection before sensitive processing",
      "Works with lightweight or stepped-up checks by patient journey",
    ],
    required: ["Identity document", "Consent", "Optional selfie"],
    steps: ["Consent", "Document", "OCR", "Policy check", "Decision"],
    providers: ["IdentityCore OCR", "Policy engine"],
    policies: [
      "Consent required before processing",
      "Route mismatch to review",
    ],
    launchChecklist: [
      "Define registration points that need identity verification",
      "Set consent copy and evidence storage requirements",
      "Map review handling for document mismatches",
      "Connect outcomes to patient admin or intake systems",
    ],
    whyItMatters: [
      "Improves confidence in patient registration data",
      "Helps teams manage consent-heavy onboarding journeys",
      "Supports safer access to sensitive healthcare services",
    ],
  },
  {
    slug: "citizen-service-access",
    title: "Citizen service access",
    category: "Government",
    description:
      "Build secure citizen verification workflows connected to internal or national identity systems.",
    icon: Building2,
    tags: ["Government", "API", "Policy"],
    audience:
      "Public agencies, civic platforms, digital registries, and national service portals.",
    outcome:
      "Confirm the citizen requesting a service is eligible and properly identified before access is granted.",
    turnaround:
      "Typical launch: varies by government integration readiness, often 2 to 6 weeks.",
    highlights: [
      "Designed for internal registries or national identity integrations",
      "Can route through multiple identity providers and agency systems",
      "Supports strong auditability for public-sector operations",
    ],
    required: ["National ID", "Selfie", "Consent"],
    steps: [
      "Consent",
      "National ID",
      "Provider route",
      "Face match",
      "Decision",
    ],
    providers: ["Government ID API", "IdentityCore workflow engine"],
    policies: [
      "Use government provider when configured",
      "Record full audit trail",
    ],
    launchChecklist: [
      "Define the citizen services that require proofing",
      "Choose fallback routing when government APIs are unavailable",
      "Document reviewer access and escalation paths",
      "Confirm audit and evidence storage requirements",
    ],
    whyItMatters: [
      "Improves trust in online public service delivery",
      "Avoids hard-coding single-provider government flows",
      "Makes compliance and incident review easier",
    ],
  },
  {
    slug: "age-verification",
    title: "Age verification",
    category: "General",
    description:
      "Confirm age eligibility using document intelligence, policy rules, and optional manual review.",
    icon: ShieldCheck,
    tags: ["Age", "Documents", "Decision"],
    audience:
      "Commerce, gaming, creator tools, media, marketplaces, and regulated digital services.",
    outcome:
      "Return a simple age eligibility decision without forcing every flow into a full onboarding process.",
    turnaround:
      "Typical launch: a few days when document-only checks are acceptable.",
    highlights: [
      "Optimized for yes or no age eligibility outcomes",
      "Can be lighter-weight than full identity onboarding",
      "Supports review for ambiguous or low-confidence extractions",
    ],
    required: ["Date-of-birth document", "Consent"],
    steps: ["Consent", "Document capture", "OCR", "Age policy", "Decision"],
    providers: ["IdentityCore OCR", "Policy engine"],
    policies: [
      "Approve only if age rule passes",
      "Manual review if OCR confidence is low",
    ],
    launchChecklist: [
      "Define the jurisdiction-specific age threshold",
      "Choose accepted documents and fallback handling",
      "Set the response format for product teams consuming the decision",
      "Define retention and deletion rules for age evidence",
    ],
    whyItMatters: [
      "Avoids over-collecting data for simple age gates",
      "Supports consistent enforcement across products",
      "Creates an auditable trail for restricted services",
    ],
  },
];

export function getTemplate(slug: string) {
  return workflowTemplates.find((template) => template.slug === slug);
}
