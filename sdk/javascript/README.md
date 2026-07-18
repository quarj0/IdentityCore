# IdentityCore JavaScript SDK

Typed, server-side JavaScript client for IdentityCore. Requires Node.js 18+.

> This package uses secret API-client credentials and intentionally rejects browser use. Call it from your server, never from client-side JavaScript.

## Quick start

```js
import { IdentityCoreClient } from "@identitycore/sdk";

const client = new IdentityCoreClient({
  apiOrigin: "https://api.identitycore.com",
  clientId: process.env.IDENTITYCORE_CLIENT_ID,
  clientSecret: process.env.IDENTITYCORE_CLIENT_SECRET,
});

const [policy] = await client.policies.list();
const verification = await client.verifications.create(
  {
    purpose: "Customer onboarding",
    policyId: policy.id,
    projectId: "prj_...",
    verificationSubject: { fullName: "Kwame Mensah", email: "kwame@example.com" },
    externalReference: "customer_123",
    redirectUrl: "https://app.example.com/identity/complete",
  },
  { idempotencyKey: "customer_123-onboarding-v1" },
);
```

GET requests retry transient failures automatically. Verification creation is idempotent and safely retried; cancellation and link resend are not retried automatically.

## Pagination and webhooks

```js
import { verifyWebhookSignature } from "@identitycore/sdk";

for await (const verification of client.verifications.iterate({ status: "verified" })) {
  console.log(verification.id);
}

const valid = verifyWebhookSignature(rawRequestBody, {
  signature: request.headers["x-identitycore-signature"],
  timestamp: request.headers["x-identitycore-timestamp"],
  signingKey: process.env.IDENTITYCORE_WEBHOOK_SECRET,
});
```

Always verify the unmodified request body before parsing JSON. The default timestamp tolerance is five minutes.
