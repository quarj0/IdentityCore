export type VerificationStep =
  | "consent"
  | "document_type"
  | "document_front"
  | "document_back"
  | "document_review"
  | "selfie"
  | "selfie_review"
  | "liveness"
  | "processing"
  | "result"
  | "submitted";

export const verificationSteps: { key: VerificationStep; label: string }[] = [
  { key: "consent", label: "Consent" },
  { key: "document_type", label: "Document" },
  { key: "document_front", label: "Front" },
  { key: "document_back", label: "Back" },
  { key: "document_review", label: "Review" },
  { key: "selfie", label: "Selfie" },
  { key: "liveness", label: "Liveness" },
  { key: "processing", label: "Processing" },
  { key: "result", label: "Result" },
];

export const mockSession = {
  id: "vfs_01HZYMOCK",
  organizationName: "Acme Financial Services",
  workflowName: "Customer onboarding",
  expiresIn: "14:58",
  subjectEmail: "person@example.com",
};

export const documentTypes = [
  "National ID",
  "Passport",
  "Driver's license",
  "Voter ID",
];

export const mockResult = {
  decision: "Approved",
  reference: "ver_01HZYMOCK",
  faceMatch: "98.7%",
  liveness: "Passed",
  ocrConfidence: "99.1%",
  documentAuthenticity: "Passed",
};
