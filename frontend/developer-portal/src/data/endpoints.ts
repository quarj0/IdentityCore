export interface EndpointExample {
  label: string;
  language: string;
  code: string;
}

export interface EndpointDefinition {
  slug: string;
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  title: string;
  description: string;
  category: string;
  request: string;
  response: string;
  examples: EndpointExample[];
}

export const endpoints: EndpointDefinition[] = [
  {
    slug: "create-workflow-session",
    method: "POST",
    path: "/api/v1/workflow-sessions",
    title: "Create workflow session",
    description:
      "Creates a hosted workflow session for verification, onboarding, or trust workflows.",
    category: "Workflow sessions",
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
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl -X POST https://api.identitycore.dev/api/v1/workflow-sessions \\
  -H "Authorization: Bearer $IDENTITYCORE_API_KEY" \\
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
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch("https://api.identitycore.dev/api/v1/workflow-sessions", {
  method: "POST",
  headers: {
    Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workflow: "customer-onboarding",
    subject: {
      email: "person@example.com",
    },
    return_url: "https://app.example.com/complete",
  }),
});

const session = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.post(
    "https://api.identitycore.dev/api/v1/workflow-sessions",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "workflow": "customer-onboarding",
        "subject": {"email": "person@example.com"},
        "return_url": "https://app.example.com/complete",
    },
)

session = response.json()`,
      },
    ],
  },
  {
    slug: "retrieve-workflow-session",
    method: "GET",
    path: "/api/v1/workflow-sessions/{id}",
    title: "Retrieve workflow session",
    description:
      "Returns the current status, subject, workflow, and latest decision for a session.",
    category: "Workflow sessions",
    request: `GET /api/v1/workflow-sessions/wfs_01HZY...`,
    response: `{
  "id": "wfs_01HZY...",
  "status": "completed",
  "decision": "approved",
  "workflow": "customer-onboarding"
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl https://api.identitycore.dev/api/v1/workflow-sessions/wfs_01HZY... \\
  -H "Authorization: Bearer $IDENTITYCORE_API_KEY"`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch(
  "https://api.identitycore.dev/api/v1/workflow-sessions/wfs_01HZY...",
  {
    headers: {
      Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
    },
  },
);

const session = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.get(
    "https://api.identitycore.dev/api/v1/workflow-sessions/wfs_01HZY...",
    headers={"Authorization": f"Bearer {IDENTITYCORE_API_KEY}"},
)

session = response.json()`,
      },
    ],
  },
  {
    slug: "create-verification-request",
    method: "POST",
    path: "/api/v1/verification-requests",
    title: "Create verification request",
    description:
      "Creates a no-code verification request that can be shared as a hosted link.",
    category: "Verification requests",
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
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl -X POST https://api.identitycore.dev/api/v1/verification-requests \\
  -H "Authorization: Bearer $IDENTITYCORE_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "workflow": "student-enrollment",
    "subject": {
      "email": "student@example.edu"
    }
  }'`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch("https://api.identitycore.dev/api/v1/verification-requests", {
  method: "POST",
  headers: {
    Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workflow: "student-enrollment",
    subject: {
      email: "student@example.edu",
    },
  }),
});

const verificationRequest = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.post(
    "https://api.identitycore.dev/api/v1/verification-requests",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "workflow": "student-enrollment",
        "subject": {"email": "student@example.edu"},
    },
)

verification_request = response.json()`,
      },
    ],
  },
  {
    slug: "list-events",
    method: "GET",
    path: "/api/v1/events",
    title: "List events",
    description:
      "Lists workflow and verification events for debugging and operational review.",
    category: "Events",
    request: `GET /api/v1/events`,
    response: `{
  "data": [
    {
      "id": "evt_01HZY...",
      "type": "workflow.session.completed"
    }
  ]
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl "https://api.identitycore.dev/api/v1/events?limit=20" \\
  -H "Authorization: Bearer $IDENTITYCORE_API_KEY"`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch("https://api.identitycore.dev/api/v1/events?limit=20", {
  headers: {
    Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
  },
});

const events = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.get(
    "https://api.identitycore.dev/api/v1/events?limit=20",
    headers={"Authorization": f"Bearer {IDENTITYCORE_API_KEY}"},
)

events = response.json()`,
      },
    ],
  },
];
