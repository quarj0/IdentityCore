export const examples = [
  {
    title: "Create a workflow session",
    language: "bash",
    code: `curl -X POST https://api.identitycore.dev/api/v1/workflow-sessions \\
  -H "Authorization: Bearer sk_test_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "workflow": "customer-onboarding",
    "subject": {
      "email": "person@example.com"
    },
    "return_url": "https://app.example.com/complete"
  }'`,
  },
  {
    title: "Webhook event",
    language: "json",
    code: `{
  "id": "evt_01HZY...",
  "type": "workflow.session.completed",
  "created_at": "2026-07-07T12:00:00Z",
  "data": {
    "session_id": "wfs_01HZY...",
    "decision": "approved",
    "workflow": "customer-onboarding"
  }
}`,
  },
];
