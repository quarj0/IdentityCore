export type WorkflowStatus = "draft" | "published" | "archived";

export type GlobalWorkflow = {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  version: string;
  category: "KYC" | "KYB" | "Education" | "Healthcare" | "Age Verification";
  linkedTemplates: string[];
  steps: string[];
  countries: string[];
  organizationsUsing: number;
  monthlyRuns: number;
  approvalRate: string;
  failureRate: string;
  lastUpdatedAt: string;
  ownerTeam: string;
};

export const globalWorkflows: GlobalWorkflow[] = [
  {
    id: "wf_standard_kyc",
    name: "Standard KYC Workflow",
    description:
      "Default KYC workflow with document verification, face match, liveness, risk scoring and manual review fallback.",
    status: "published",
    version: "v2.3.0",
    category: "KYC",
    linkedTemplates: ["Ghana Card Standard KYC", "Banking Tier 2 KYC"],
    steps: [
      "Collect user consent",
      "Capture identity document",
      "Run OCR extraction",
      "Run face match",
      "Run liveness check",
      "Calculate risk score",
      "Route to manual review if needed",
      "Send webhook result",
    ],
    countries: ["Ghana", "Nigeria", "Kenya"],
    organizationsUsing: 142,
    monthlyRuns: 184200,
    approvalRate: "91.8%",
    failureRate: "6.4%",
    lastUpdatedAt: "2026-07-05",
    ownerTeam: "Product Platform",
  },
  {
    id: "wf_bank_high_risk",
    name: "Banking High-Risk Review",
    description:
      "Enhanced due diligence workflow for regulated financial institutions and higher-risk user segments.",
    status: "published",
    version: "v1.8.4",
    category: "KYC",
    linkedTemplates: ["Banking Tier 2 KYC"],
    steps: [
      "Collect consent",
      "Verify government ID",
      "Check address evidence",
      "Run watchlist screening",
      "Run fraud signals",
      "Escalate to senior reviewer",
      "Generate compliance report",
    ],
    countries: ["Ghana", "Nigeria"],
    organizationsUsing: 38,
    monthlyRuns: 42300,
    approvalRate: "84.2%",
    failureRate: "10.9%",
    lastUpdatedAt: "2026-06-29",
    ownerTeam: "Risk Team",
  },
  {
    id: "wf_student_onboarding",
    name: "Student Onboarding Workflow",
    description:
      "Education workflow for schools, universities, exams and learning platforms.",
    status: "draft",
    version: "v0.7.0",
    category: "Education",
    linkedTemplates: ["Student Identity Verification"],
    steps: [
      "Verify student email",
      "Capture student ID",
      "Run face match",
      "Confirm institution domain",
      "Approve or queue for review",
    ],
    countries: ["Ghana", "Kenya"],
    organizationsUsing: 0,
    monthlyRuns: 0,
    approvalRate: "N/A",
    failureRate: "N/A",
    lastUpdatedAt: "2026-07-08",
    ownerTeam: "Education Team",
  },
  {
    id: "wf_patient_identity",
    name: "Patient Identity Workflow",
    description:
      "Healthcare identity workflow with consent, patient ID verification and privacy-first retention.",
    status: "published",
    version: "v1.1.2",
    category: "Healthcare",
    linkedTemplates: ["Healthcare Patient Verification"],
    steps: [
      "Capture consent",
      "Verify government ID",
      "Run face match",
      "Apply retention rule",
      "Send result to provider",
    ],
    countries: ["Ghana", "South Africa", "Kenya"],
    organizationsUsing: 26,
    monthlyRuns: 18200,
    approvalRate: "93.4%",
    failureRate: "4.7%",
    lastUpdatedAt: "2026-06-23",
    ownerTeam: "Compliance Team",
  },
  {
    id: "wf_age_gate",
    name: "Age Gate Workflow",
    description:
      "Minimal-data age verification workflow for age-restricted services.",
    status: "archived",
    version: "v1.0.0",
    category: "Age Verification",
    linkedTemplates: ["Age Restricted Access"],
    steps: [
      "Capture age document",
      "Extract date of birth",
      "Apply age policy",
      "Return pass/fail result",
    ],
    countries: ["Ghana", "Nigeria"],
    organizationsUsing: 7,
    monthlyRuns: 2110,
    approvalRate: "89.1%",
    failureRate: "8.2%",
    lastUpdatedAt: "2026-05-18",
    ownerTeam: "Policy Team",
  },
];

export const workflowVersions = [
  {
    version: "v2.3.0",
    status: "Current",
    date: "2026-07-05",
    notes: "Added improved risk routing and better webhook retry metadata.",
  },
  {
    version: "v2.2.0",
    status: "Superseded",
    date: "2026-06-11",
    notes: "Updated manual review escalation thresholds.",
  },
  {
    version: "v2.1.0",
    status: "Superseded",
    date: "2026-05-03",
    notes: "Added liveness step as mandatory for high-risk flows.",
  },
];

export const workflowUsage = [
  {
    organization: "Ghana FinTrust Bank",
    environment: "Production",
    runs: "48,210",
  },
  {
    organization: "LagosPay",
    environment: "Production",
    runs: "31,490",
  },
  {
    organization: "EduVerify Africa",
    environment: "Sandbox",
    runs: "8,720",
  },
];

export function getWorkflowById(workflowId: string) {
  return globalWorkflows.find((workflow) => workflow.id === workflowId);
}