export type DocPage = {
  title: string;
  description: string;
  path: string;
  group: string;
  sections: Array<{
    heading: string;
    body: string;
    code?: string;
  }>;
};

export const dashboardUrl = process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000";
export const productSiteUrl = process.env.NEXT_PUBLIC_MARKETING_URL ?? "http://localhost:3001";

export const docGroups = [
  {
    title: "Getting started",
    items: [
      { label: "Quickstart", path: "/quickstart" },
      { label: "Authentication", path: "/authentication" },
      { label: "Error handling", path: "/error-handling" },
    ],
  },
  {
    title: "Core API",
    items: [
      { label: "Create verification", path: "/api/verifications/create" },
      { label: "Retrieve verification", path: "/api/verifications/demo-verification" },
      { label: "Policies", path: "/api/policies" },
    ],
  },
  {
    title: "Platform",
    items: [
      { label: "Webhooks", path: "/platform/webhooks" },
      { label: "Review queues", path: "/platform/review-queues" },
      { label: "Audit exports", path: "/platform/audit-exports" },
    ],
  },
  {
    title: "Tools",
    items: [
      { label: "Sandbox", path: "/sandbox" },
      { label: "Testing tools", path: "/testing-tools" },
      { label: "Node SDK", path: "/sdk/node" },
      { label: "Python SDK", path: "/sdk/python" },
      { label: "Error reference", path: "/reference/errors" },
    ],
  },
];

export const docPages: Record<string, DocPage> = {
  "/quickstart": {
    title: "Quickstart",
    description: "Create a verification session server-side, redirect the subject, and react to the final outcome.",
    path: "/quickstart",
    group: "Getting started",
    sections: [
      {
        heading: "1. Create a secret key",
        body: "Generate a server-side key from the dashboard and store it in your backend environment. Never expose live secrets in client code.",
        code: "IDENTITYCORE_SECRET_KEY=ic_live_sk_...",
      },
      {
        heading: "2. Create a session",
        body: "POST a policy ID, the subject payload, and your own internal metadata to create the hosted verification link.",
        code: `curl -X POST https://api.identitycore.com/v1/verifications \\
  -H "Authorization: Bearer ic_live_sk_..." \\
  -H "Content-Type: application/json" \\
  -d '{"policy_id":"pol-standard-kyc","email":"user@example.com"}'`,
      },
      {
        heading: "3. Process results",
        body: "Listen for webhook events, fetch the final verification object, and branch your product workflow on approved, review, or rejected outcomes.",
      },
    ],
  },
  "/authentication": {
    title: "Authentication",
    description: "Use bearer secret keys for server-side API calls and rotate them regularly.",
    path: "/authentication",
    group: "Getting started",
    sections: [
      {
        heading: "Secret keys",
        body: "Every request to the REST API must include a bearer token. Use separate test and live keys for environment isolation.",
      },
      {
        heading: "Rotation",
        body: "Prefer one key per service or deployment surface so rotation is scoped and observable.",
      },
    ],
  },
  "/error-handling": {
    title: "Error handling",
    description: "Plan for validation, auth, idempotency, and provider-side failures from the start.",
    path: "/error-handling",
    group: "Getting started",
    sections: [
      {
        heading: "Validation failures",
        body: "4xx responses usually indicate malformed payloads, unsupported policy references, or missing required subject fields.",
      },
      {
        heading: "Retries",
        body: "Retry only idempotent network failures. Avoid blind retries for validation or authorization errors.",
      },
    ],
  },
  "/api/verifications/create": {
    title: "Create verification",
    description: "Create a hosted verification session with policy, subject, and metadata inputs.",
    path: "/api/verifications/create",
    group: "Core API",
    sections: [
      {
        heading: "Required inputs",
        body: "A verification request generally needs a policy ID, a contact method, and enough subject metadata to link the outcome back to your system.",
      },
      {
        heading: "Response shape",
        body: "The API returns the session identifier, hosted URL, initial status, and timestamps for auditing and follow-up polling.",
      },
    ],
  },
  "/api/verifications/demo-verification": {
    title: "Retrieve verification",
    description: "Fetch the current state, evidence summary, and decision lifecycle for a verification.",
    path: "/api/verifications/demo-verification",
    group: "Core API",
    sections: [
      {
        heading: "Polling vs webhooks",
        body: "Use webhooks as your primary trigger. Retrieval endpoints are ideal for dashboards, support tools, and confirmation reads.",
      },
      {
        heading: "Decision objects",
        body: "The retrieved verification should expose status, final decision, reasons, and any reviewer annotations your operators depend on.",
      },
    ],
  },
  "/api/policies": {
    title: "Policies",
    description: "Manage reusable verification requirements for document, selfie, liveness, and manual-review behavior.",
    path: "/api/policies",
    group: "Core API",
    sections: [
      {
        heading: "Policy design",
        body: "Policies should represent stable business rules, not one-off ad hoc sessions. Keep them versioned and traceable.",
      },
      {
        heading: "Parity with dashboard",
        body: "API-created policies and dashboard-created policies map to the same backend policy model.",
      },
    ],
  },
  "/platform/webhooks": {
    title: "Webhooks",
    description: "Subscribe to verification lifecycle events and validate signatures on every delivery.",
    path: "/platform/webhooks",
    group: "Platform",
    sections: [
      {
        heading: "Signature verification",
        body: "Always validate the HMAC signature before trusting the payload, and reject stale timestamps.",
      },
      {
        heading: "Delivery health",
        body: "Track 2xx rate, median latency, and retry volume by endpoint so degraded consumers surface quickly.",
      },
    ],
  },
  "/platform/review-queues": {
    title: "Review queues",
    description: "Manual-review decisions move through the same platform queues used by operational teams.",
    path: "/platform/review-queues",
    group: "Platform",
    sections: [
      {
        heading: "Queue entry",
        body: "Sessions land in review when automated confidence falls below threshold or provider checks conflict.",
      },
      {
        heading: "Operational expectations",
        body: "Design internal workflows around queue assignment, turnaround SLAs, and evidence visibility.",
      },
    ],
  },
  "/platform/audit-exports": {
    title: "Audit exports",
    description: "Export decisions, access events, and reviewer actions for compliance and operational reporting.",
    path: "/platform/audit-exports",
    group: "Platform",
    sections: [
      {
        heading: "Export scope",
        body: "Audit exports should cover policy changes, reviewer actions, verification decisions, and access-sensitive events.",
      },
      {
        heading: "Retention",
        body: "Align export frequency and destination with your own compliance retention obligations.",
      },
    ],
  },
  "/sandbox": {
    title: "Sandbox",
    description: "Use test API keys, sample policies, and predictable mock outcomes before moving to production.",
    path: "/sandbox",
    group: "Tools",
    sections: [
      {
        heading: "Environment separation",
        body: "Keep sandbox traffic, keys, and endpoints isolated so tests never leak into production workflows.",
      },
      {
        heading: "Mock outcomes",
        body: "Sandbox should support deterministic approvals, reviews, and rejections for integration testing.",
      },
    ],
  },
  "/testing-tools": {
    title: "Testing tools",
    description: "Use mock sessions, event replay, and fixture payloads to harden your integration.",
    path: "/testing-tools",
    group: "Tools",
    sections: [
      {
        heading: "Fixture strategy",
        body: "Store representative approved, review, rejected, and expired payloads in your own test suite.",
      },
      {
        heading: "Replay",
        body: "Webhook replay is the quickest path for validating consumer resilience after code or infrastructure changes.",
      },
    ],
  },
  "/sdk/node": {
    title: "Node SDK",
    description: "Use the Node SDK for typed session creation, retrieval, and webhook handling in JavaScript runtimes.",
    path: "/sdk/node",
    group: "Tools",
    sections: [
      {
        heading: "Client setup",
        body: "Create one server-side SDK client per process or request lifecycle, depending on your runtime model.",
        code: `import { IdentityCore } from "@identitycore/sdk";

const client = new IdentityCore({
  apiKey: process.env.IDENTITYCORE_SECRET_KEY!,
});`,
      },
    ],
  },
  "/sdk/python": {
    title: "Python SDK",
    description: "Use the Python client for backend jobs, orchestration workers, and service-side verification workflows.",
    path: "/sdk/python",
    group: "Tools",
    sections: [
      {
        heading: "Client setup",
        body: "Instantiate the Python client with a live or test API key in a trusted backend environment.",
        code: `from identitycore import Client

client = Client(api_key="ic_live_sk_...")`,
      },
    ],
  },
  "/reference/errors": {
    title: "Error reference",
    description: "Map platform error classes to user messaging, retries, and operational escalation paths.",
    path: "/reference/errors",
    group: "Tools",
    sections: [
      {
        heading: "Authorization errors",
        body: "Treat auth failures as operator-facing issues. Retry only after secret rotation or config correction.",
      },
      {
        heading: "Provider and upload errors",
        body: "Surface user-friendly retry guidance while retaining raw error codes for internal debugging.",
      },
    ],
  },
};

export function getDocPage(path: string) {
  return docPages[path];
}
