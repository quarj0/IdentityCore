import type { EndpointExample } from "@/data/endpoints";

export interface ExampleGroup {
  title: string;
  description: string;
  samples: EndpointExample[];
}

export const examples: ExampleGroup[] = [
  {
    title: "Create a verification",
    description:
      "Start a hosted verification from your backend in the language your team already uses.",
    samples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl -X POST https://api.identitycore.dev/api/v1/verifications/ \\
  -H "Authorization: Bearer $IDENTITYCORE_API_KEY" \\
  -H "X-Client-Id: api_client_id" \\
  -H "Content-Type: application/json" \\
  -d '{
    "purpose": "Customer onboarding",
    "policy_id": "pol_01JABC...",
    "verification_subject": {
      "full_name": "Amina Mensah",
      "email": "amina@example.com"
    },
    "redirect_url": "https://app.example.com/verification-complete",
    "metadata": {
      "customer_id": "customer_12345"
    }
  }'`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch("https://api.identitycore.dev/api/v1/verifications/", {
  method: "POST",
  headers: {
    Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
    "X-Client-Id": process.env.IDENTITYCORE_CLIENT_ID ?? "",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    purpose: "Customer onboarding",
    policy_id: "pol_01JABC...",
    verification_subject: {
      full_name: "Amina Mensah",
      email: "amina@example.com",
    },
    redirect_url: "https://app.example.com/verification-complete",
    metadata: {
      customer_id: "customer_12345",
    },
  }),
});

const verification = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.post(
    "https://api.identitycore.dev/api/v1/verifications/",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "X-Client-Id": IDENTITYCORE_CLIENT_ID,
        "Content-Type": "application/json",
    },
    json={
        "purpose": "Customer onboarding",
        "policy_id": "pol_01JABC...",
        "verification_subject": {
            "full_name": "Amina Mensah",
            "email": "amina@example.com",
        },
        "redirect_url": "https://app.example.com/verification-complete",
        "metadata": {"customer_id": "customer_12345"},
    },
)

verification = response.json()`,
      },
    ],
  },
  {
    title: "Webhook event",
    description:
      "Inspect the shape of a verification event before you wire up signature verification and retries.",
    samples: [
      {
        label: "JSON payload",
        language: "json",
        code: `{
  "id": "evt_01HZY...",
  "type": "verification.verified",
  "created_at": "2026-07-07T12:00:00Z",
  "data": {
    "verification_id": "ver_01HZY...",
    "status": "verified"
  }
}`,
      },
      {
        label: "TypeScript handler",
        language: "ts",
        code: `export async function POST(request: Request) {
  const payload = await request.json();

  if (payload.type === "verification.verified") {
    await markCustomerVerified(payload.data.verification_id);
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

    if payload["type"] == "verification.verified":
        mark_customer_verified(payload["data"]["verification_id"])

    return ("", 204)`,
      },
    ],
  },
];
