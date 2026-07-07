export const endpoints = [
  {
    slug: "create-workflow-session",
    method: "POST",
    path: "/api/v1/workflow-sessions",
    title: "Create workflow session",
    description:
      "Creates a hosted workflow session for verification, onboarding, or trust workflows.",
    request: `{
  "workflow": "customer-onboarding",
  "subject": {
    "email": "person@example.com"
  },
  "return_url": "https://app.example.com/complete"
}`,
    response: `{
  "id": "wfs_01HZY...",
  "status": "created",
  "verification_url": "https://verify.identitycore.dev/session/wfs_01HZY..."
}`,
  },
  {
    slug: "retrieve-workflow-session",
    method: "GET",
    path: "/api/v1/workflow-sessions/{id}",
    title: "Retrieve workflow session",
    description:
      "Returns the current status, subject, workflow, and latest decision for a session.",
    request: `GET /api/v1/workflow-sessions/wfs_01HZY...`,
    response: `{
  "id": "wfs_01HZY...",
  "status": "completed",
  "decision": "approved",
  "workflow": "customer-onboarding"
}`,
  },
  {
    slug: "create-verification-request",
    method: "POST",
    path: "/api/v1/verification-requests",
    title: "Create verification request",
    description:
      "Creates a no-code verification request that can be shared as a hosted link.",
    request: `{
  "workflow": "student-enrollment",
  "subject": {
    "email": "student@example.edu"
  }
}`,
    response: `{
  "id": "vrq_01HZY...",
  "status": "created",
  "url": "https://verify.identitycore.dev/request/vrq_01HZY..."
}`,
  },
  {
    slug: "list-events",
    method: "GET",
    path: "/api/v1/events",
    title: "List events",
    description:
      "Lists workflow and verification events for debugging and operational review.",
    request: `GET /api/v1/events`,
    response: `{
  "data": [
    {
      "id": "evt_01HZY...",
      "type": "workflow.session.completed"
    }
  ]
}`,
  },
];
