import type { EndpointExample } from "@/data/endpoints";

export interface ExampleGroup {
  title: string;
  description: string;
  samples: EndpointExample[];
}

export const examples: ExampleGroup[] = [
  {
    title: "Create a workflow session",
    description:
      "Start a hosted onboarding flow from your backend in the language your team already uses.",
    samples: [
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
    title: "Webhook event",
    description:
      "Inspect the shape of a completed workflow event before you wire up signature verification and retries.",
    samples: [
      {
        label: "JSON payload",
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
      {
        label: "TypeScript handler",
        language: "ts",
        code: `export async function POST(request: Request) {
  const payload = await request.json();

  if (payload.type === "workflow.session.completed") {
    await markCustomerVerified(payload.data.session_id, payload.data.decision);
  }

  return new Response(null, { status: 204 });
}`,
      },
      {
        label: "Python handler",
        language: "python",
        code: `from flask import Flask, request

app = Flask(__name__)

@app.post("/webhooks/identitycore")
def handle_identitycore_webhook():
    payload = request.get_json()

    if payload["type"] == "workflow.session.completed":
        mark_customer_verified(
            payload["data"]["session_id"],
            payload["data"]["decision"],
        )

    return ("", 204)`,
      },
    ],
  },
];
