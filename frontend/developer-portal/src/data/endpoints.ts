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

const apiClientHeaders = `  -H "Authorization: Bearer $IDENTITYCORE_API_KEY" \\
  -H "X-Client-Id: api_client_id"`;

export const endpoints: EndpointDefinition[] = [
  {
    slug: "health",
    method: "GET",
    path: "/api/v1/health",
    title: "Health check",
    description: "Checks that the API is up and reports the active service version.",
    category: "Core",
    request: `GET /api/v1/health`,
    response: `{
  "success": true,
  "data": {
    "status": "ok",
    "service": "django",
    "version": "0.1.0"
  },
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl https://api.identitycore.dev/api/v1/health`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch("https://api.identitycore.dev/api/v1/health");
const health = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.get("https://api.identitycore.dev/api/v1/health")
health = response.json()`,
      },
    ],
  },
  {
    slug: "list-policies",
    method: "GET",
    path: "/api/v1/policies/",
    title: "List verification policies",
    description: "Returns the active verification policies available to the current tenant.",
    category: "Policies",
    request: `GET /api/v1/policies/`,
    response: `{
  "success": true,
  "data": [
    {
      "id": "pol_01JABC...",
      "name": "Default verification",
      "version": 1,
      "status": "active",
      "required_document_types": ["passport", "national_id"]
    }
  ],
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl https://api.identitycore.dev/api/v1/policies/ \\
${apiClientHeaders}`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch("https://api.identitycore.dev/api/v1/policies/", {
  headers: {
    Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
    "X-Client-Id": process.env.IDENTITYCORE_CLIENT_ID ?? "",
  },
});

const policies = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.get(
    "https://api.identitycore.dev/api/v1/policies/",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "X-Client-Id": IDENTITYCORE_CLIENT_ID,
    },
)

policies = response.json()`,
      },
    ],
  },
  {
    slug: "get-policy",
    method: "GET",
    path: "/api/v1/policies/{policy_id}",
    title: "Retrieve verification policy",
    description: "Returns a single active policy template by public identifier.",
    category: "Policies",
    request: `GET /api/v1/policies/pol_01JABC...`,
    response: `{
  "success": true,
  "data": {
    "id": "pol_01JABC...",
    "name": "Default verification",
    "version": 1,
    "status": "active",
    "required_document_types": ["passport", "national_id"]
  },
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl https://api.identitycore.dev/api/v1/policies/pol_01JABC... \\
${apiClientHeaders}`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch("https://api.identitycore.dev/api/v1/policies/pol_01JABC...", {
  headers: {
    Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
    "X-Client-Id": process.env.IDENTITYCORE_CLIENT_ID ?? "",
  },
});

const policy = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.get(
    "https://api.identitycore.dev/api/v1/policies/pol_01JABC...",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "X-Client-Id": IDENTITYCORE_CLIENT_ID,
    },
)

policy = response.json()`,
      },
    ],
  },
  {
    slug: "list-verifications",
    method: "GET",
    path: "/api/v1/verifications/",
    title: "List verifications",
    description: "Lists verifications for the current tenant, including status and policy links.",
    category: "Verifications",
    request: `GET /api/v1/verifications/`,
    response: `{
  "success": true,
  "data": {
    "results": [
      {
        "id": "ver_01JABC...",
        "status": "verified",
        "purpose": "Customer onboarding",
        "external_reference": "customer_12345"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  },
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl https://api.identitycore.dev/api/v1/verifications/ \\
${apiClientHeaders}`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch("https://api.identitycore.dev/api/v1/verifications/", {
  headers: {
    Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
    "X-Client-Id": process.env.IDENTITYCORE_CLIENT_ID ?? "",
  },
});

const verifications = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.get(
    "https://api.identitycore.dev/api/v1/verifications/",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "X-Client-Id": IDENTITYCORE_CLIENT_ID,
    },
)

verifications = response.json()`,
      },
    ],
  },
  {
    slug: "create-verification",
    method: "POST",
    path: "/api/v1/verifications/",
    title: "Create verification",
    description: "Creates a hosted verification from a policy and subject payload.",
    category: "Verifications",
    request: `{
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
}`,
    response: `{
  "success": true,
  "data": {
    "id": "ver_01JABC...",
    "status": "pending_consent",
    "verification_url": "https://verify.identitycore.dev/.../ver_01JABC...",
    "session_id": "ses_01JABC...",
    "session_token": "sess_token_01JABC...",
    "expires_at": "2026-07-12T16:00:00Z"
  },
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl -X POST https://api.identitycore.dev/api/v1/verifications/ \\
${apiClientHeaders} \\
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
    slug: "get-verification",
    method: "GET",
    path: "/api/v1/verifications/{verification_id}",
    title: "Retrieve verification",
    description: "Returns the verification summary and the linked policy and subject details.",
    category: "Verifications",
    request: `GET /api/v1/verifications/ver_01JABC...`,
    response: `{
  "success": true,
  "data": {
    "id": "ver_01JABC...",
    "status": "verified",
    "purpose": "Customer onboarding",
    "external_reference": "customer_12345"
  },
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl https://api.identitycore.dev/api/v1/verifications/ver_01JABC... \\
${apiClientHeaders}`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch(
  "https://api.identitycore.dev/api/v1/verifications/ver_01JABC...",
  {
    headers: {
      Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
      "X-Client-Id": process.env.IDENTITYCORE_CLIENT_ID ?? "",
    },
  },
);

const verification = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.get(
    "https://api.identitycore.dev/api/v1/verifications/ver_01JABC...",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "X-Client-Id": IDENTITYCORE_CLIENT_ID,
    },
)

verification = response.json()`,
      },
    ],
  },
  {
    slug: "cancel-verification",
    method: "POST",
    path: "/api/v1/verifications/{verification_id}/cancel",
    title: "Cancel verification",
    description: "Cancels an active verification and marks linked sessions revoked.",
    category: "Verifications",
    request: `{
  "reason": "Customer asked to stop the process"
}`,
    response: `{
  "success": true,
  "data": {
    "id": "ver_01JABC...",
    "status": "cancelled"
  },
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl -X POST https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../cancel \\
${apiClientHeaders} \\
  -H "Content-Type: application/json" \\
  -d '{"reason":"Customer asked to stop the process"}'`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch(
  "https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../cancel",
  {
    method: "POST",
    headers: {
      Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
      "X-Client-Id": process.env.IDENTITYCORE_CLIENT_ID ?? "",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ reason: "Customer asked to stop the process" }),
  },
);

const cancelledVerification = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.post(
    "https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../cancel",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "X-Client-Id": IDENTITYCORE_CLIENT_ID,
        "Content-Type": "application/json",
    },
    json={"reason": "Customer asked to stop the process"},
)

cancelled_verification = response.json()`,
      },
    ],
  },
  {
    slug: "resend-verification-link",
    method: "POST",
    path: "/api/v1/verifications/{verification_id}/resend-link",
    title: "Resend verification link",
    description: "Issues a fresh hosted link when a customer needs a new access window.",
    category: "Verifications",
    request: `{
  "channel": "email"
}`,
    response: `{
  "success": true,
  "data": {
    "sent": true,
    "verification_url": "https://verify.identitycore.dev/.../ver_01JABC...",
    "session_id": "ses_01JABC...",
    "session_token": "sess_token_01JABC...",
    "expires_at": "2026-07-12T16:30:00Z",
    "channel": "email"
  },
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl -X POST https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../resend-link \\
${apiClientHeaders} \\
  -H "Content-Type: application/json" \\
  -d '{"channel":"email"}'`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch(
  "https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../resend-link",
  {
    method: "POST",
    headers: {
      Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
      "X-Client-Id": process.env.IDENTITYCORE_CLIENT_ID ?? "",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ channel: "email" }),
  },
);

const refreshedLink = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.post(
    "https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../resend-link",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "X-Client-Id": IDENTITYCORE_CLIENT_ID,
        "Content-Type": "application/json",
    },
    json={"channel": "email"},
)

refreshed_link = response.json()`,
      },
    ],
  },
  {
    slug: "evidence-report",
    method: "GET",
    path: "/api/v1/verifications/{verification_id}/evidence-report",
    title: "Get evidence report",
    description: "Returns the report and download URLs for a completed verification.",
    category: "Verifications",
    request: `GET /api/v1/verifications/ver_01JABC.../evidence-report`,
    response: `{
  "success": true,
  "data": {
    "verification_id": "ver_01JABC...",
    "storage_key": "tenants/ten_01JABC/verifications/ver_01JABC/report.json",
    "download_url": "https://files.identitycore.dev/...",
    "pdf_storage_key": "tenants/ten_01JABC/verifications/ver_01JABC/report.pdf",
    "pdf_download_url": "https://files.identitycore.dev/..."
  },
  "request_id": "req_01JABC..."
}`,
    examples: [
      {
        label: "cURL",
        language: "bash",
        code: `curl https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../evidence-report \\
${apiClientHeaders}`,
      },
      {
        label: "TypeScript",
        language: "ts",
        code: `const response = await fetch(
  "https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../evidence-report",
  {
    headers: {
      Authorization: \`Bearer \${process.env.IDENTITYCORE_API_KEY}\`,
      "X-Client-Id": process.env.IDENTITYCORE_CLIENT_ID ?? "",
    },
  },
);

const evidenceReport = await response.json();`,
      },
      {
        label: "Python",
        language: "python",
        code: `import requests

response = requests.get(
    "https://api.identitycore.dev/api/v1/verifications/ver_01JABC.../evidence-report",
    headers={
        "Authorization": f"Bearer {IDENTITYCORE_API_KEY}",
        "X-Client-Id": IDENTITYCORE_CLIENT_ID,
    },
)

evidence_report = response.json()`,
      },
    ],
  },
];
