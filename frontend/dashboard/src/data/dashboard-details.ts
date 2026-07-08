export const detailTimeline = [
  {
    title: "Created",
    description: "Resource was created in sandbox.",
    time: "Just now",
  },
  {
    title: "Configured",
    description: "Default settings were applied.",
    time: "Just now",
  },
  {
    title: "Ready",
    description: "Resource is ready for integration.",
    time: "Just now",
  },
];

export const verificationEvidence = {
  decision: "approved",
  face_match_score: 98.7,
  liveness: "passed",
  ocr_confidence: 99.1,
  policy_version: "policy_v1",
  provider: "identitycore_mock",
};

export const workflowNodes = [
  "Start",
  "Consent",
  "Document capture",
  "OCR",
  "Selfie",
  "Liveness",
  "Face match",
  "Policy decision",
  "Webhook",
];
