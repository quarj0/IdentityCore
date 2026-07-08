export const mockSession = {
  id: "vfs_01HZYMOCK",
  organizationName: "Acme Financial Services",
  workflowName: "Customer onboarding",
  status: "active",
  expiresIn: "14:58",
  subject: {
    email: "person@example.com",
  },
  requirements: [
    "Consent",
    "Identity document",
    "Selfie capture",
    "Liveness check",
    "Final review",
  ],
};

export const resultStates = {
  approved: {
    decision: "Approved",
    tone: "success",
    description: "Your verification was completed successfully.",
  },
  review: {
    decision: "Needs review",
    tone: "warning",
    description:
      "Your verification was submitted and requires manual review by the organization.",
  },
  rejected: {
    decision: "Rejected",
    tone: "danger",
    description:
      "The verification could not be approved based on the submitted evidence.",
  },
};

export const mockResult = {
  decision: "Approved",
  faceMatch: "98.7%",
  liveness: "Passed",
  ocrConfidence: "99.1%",
  documentAuthenticity: "Passed",
  reference: "ver_01HZYMOCK",
};
