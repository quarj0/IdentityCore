export type ReviewCaseStatus =
  | "pending"
  | "assigned"
  | "escalated"
  | "approved"
  | "rejected";

export type ReviewCasePriority = "low" | "medium" | "high" | "critical";

export type ReviewCase = {
  id: string;
  applicantName: string;
  organizationName: string;
  organizationId: string;
  status: ReviewCaseStatus;
  priority: ReviewCasePriority;
  country: string;
  documentType: string;
  riskScore: number;
  aiRecommendation: "Approve" | "Reject" | "Manual review";
  failureReason: string;
  assignedTo: string;
  createdAt: string;
  slaDueAt: string;
  checks: string[];
};

export const reviewCases: ReviewCase[] = [
  {
    id: "case_1001",
    applicantName: "Kwame Boateng",
    organizationName: "Ghana FinTrust Bank",
    organizationId: "org_ghana_fintrust",
    status: "pending",
    priority: "high",
    country: "Ghana",
    documentType: "Ghana Card",
    riskScore: 72,
    aiRecommendation: "Manual review",
    failureReason: "Face match confidence below threshold",
    assignedTo: "Unassigned",
    createdAt: "2026-07-09 09:21",
    slaDueAt: "2026-07-09 11:21",
    checks: ["Document OCR", "Face match", "Liveness", "Risk score"],
  },
  {
    id: "case_1002",
    applicantName: "Amina Yusuf",
    organizationName: "LagosPay",
    organizationId: "org_lagos_pay",
    status: "assigned",
    priority: "medium",
    country: "Nigeria",
    documentType: "NIN",
    riskScore: 54,
    aiRecommendation: "Manual review",
    failureReason: "OCR confidence below policy threshold",
    assignedTo: "Ama Mensah",
    createdAt: "2026-07-09 08:55",
    slaDueAt: "2026-07-09 12:55",
    checks: ["OCR", "Document quality", "Risk score"],
  },
  {
    id: "case_1003",
    applicantName: "Grace Wanjiku",
    organizationName: "Civic Registry Authority",
    organizationId: "org_civic_registry",
    status: "escalated",
    priority: "critical",
    country: "Kenya",
    documentType: "National ID",
    riskScore: 91,
    aiRecommendation: "Reject",
    failureReason: "Potential document tampering detected",
    assignedTo: "Tunde Adebayo",
    createdAt: "2026-07-09 08:10",
    slaDueAt: "2026-07-09 10:10",
    checks: ["Document authentication", "Fraud signal", "Senior review"],
  },
  {
    id: "case_1004",
    applicantName: "Nandi Khumalo",
    organizationName: "HealthPass Clinics",
    organizationId: "org_healthpass",
    status: "approved",
    priority: "low",
    country: "South Africa",
    documentType: "National ID",
    riskScore: 21,
    aiRecommendation: "Approve",
    failureReason: "Reviewer approved after consent confirmation",
    assignedTo: "Sarah Mitchell",
    createdAt: "2026-07-09 07:42",
    slaDueAt: "Completed",
    checks: ["Consent", "Face match", "Document OCR"],
  },
];

export const reviewerPerformance = [
  {
    reviewer: "Ama Mensah",
    assigned: 42,
    completed: 38,
    accuracy: "97.4%",
    avgHandleTime: "4m 12s",
  },
  {
    reviewer: "Tunde Adebayo",
    assigned: 31,
    completed: 28,
    accuracy: "96.1%",
    avgHandleTime: "5m 08s",
  },
  {
    reviewer: "Sarah Mitchell",
    assigned: 26,
    completed: 24,
    accuracy: "98.2%",
    avgHandleTime: "3m 44s",
  },
];

export const reviewEvidence = [
  {
    label: "Document OCR",
    value: "Name and date of birth extracted with 84% confidence",
  },
  {
    label: "Face match",
    value: "Similarity score 71%, below configured threshold of 78%",
  },
  {
    label: "Liveness",
    value: "Passed passive liveness with medium confidence",
  },
  {
    label: "Risk engine",
    value: "Elevated due to mismatch and previous failed attempt",
  },
];

export const qualityChecklist = [
  "Reviewer confirmed document visibility",
  "Reviewer compared extracted text with document image",
  "Reviewer checked policy reason before decision",
  "Reviewer added internal decision note",
];

export function getReviewCaseById(caseId: string) {
  return reviewCases.find((reviewCase) => reviewCase.id === caseId);
}