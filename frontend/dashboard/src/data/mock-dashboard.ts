export const workspace = {
  organizationName: "Acme Financial Services",
  tier: "Tier 0 — Trial",
  environment: "Sandbox",
  status: "Onboarding required",
};

export const metrics = [
  {
    label: "Workflow sessions",
    value: "0",
    description: "No production traffic yet",
  },
  {
    label: "Pending reviews",
    value: "0",
    description: "Manual review queue",
  },
  {
    label: "Active workflows",
    value: "0",
    description: "Create or clone a workflow",
  },
  {
    label: "API keys",
    value: "1",
    description: "Sandbox key available",
  },
];

export const onboardingSteps = [
  {
    title: "Email verified",
    description: "Administrator account activated.",
    status: "complete",
  },
  {
    title: "Organization profile",
    description: "Add legal and business information.",
    status: "current",
  },
  {
    title: "Organization verification",
    description: "Upload supporting organization documents.",
    status: "upcoming",
  },
  {
    title: "Administrator identity",
    description: "Verify the primary workspace administrator.",
    status: "upcoming",
  },
  {
    title: "First workflow",
    description: "Create or clone your first workflow.",
    status: "upcoming",
  },
  {
    title: "Production approval",
    description: "Submit workspace for production access.",
    status: "upcoming",
  },
];

export const recentActivity = [
  {
    title: "Workspace created",
    description: "Acme Financial Services workspace was created.",
    time: "Just now",
  },
  {
    title: "Sandbox enabled",
    description: "Sandbox environment is available for testing.",
    time: "Just now",
  },
  {
    title: "Onboarding started",
    description: "Complete onboarding to request production access.",
    time: "Just now",
  },
];
