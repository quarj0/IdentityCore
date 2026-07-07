export const endpoints = [
  {
    method: "POST",
    path: "/api/v1/workflow-sessions",
    title: "Create workflow session",
    description:
      "Creates a hosted workflow session for verification, onboarding, or trust workflows.",
  },
  {
    method: "GET",
    path: "/api/v1/workflow-sessions/{id}",
    title: "Retrieve workflow session",
    description:
      "Returns the current status, subject, workflow, and latest decision for a session.",
  },
  {
    method: "POST",
    path: "/api/v1/verification-requests",
    title: "Create verification request",
    description:
      "Creates a no-code verification request that can be shared as a hosted link.",
  },
  {
    method: "GET",
    path: "/api/v1/events",
    title: "List events",
    description:
      "Lists workflow and verification events for debugging and operational review.",
  },
];
