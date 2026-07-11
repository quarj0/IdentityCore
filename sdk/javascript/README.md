# IdentityCore JavaScript SDK

JavaScript client for IdentityCore public REST APIs. It mirrors the Python SDK and uses API-client credentials.

## Quick start

```js
import { IdentityCoreClient } from "@identitycore/sdk";

const client = new IdentityCoreClient({
  apiOrigin: "https://api.identitycore.com",
  clientId: "cli_...",
  clientSecret: "...",
});

const policies = await client.policies.list();

const verification = await client.verifications.create({
  purpose: "Customer onboarding",
  policyId: policies[0].id,
  verificationSubject: {
    fullName: "Kwame Mensah",
    email: "kwame@example.com",
  },
  externalReference: "customer_123",
});

console.log(verification.verification_url);
```

## Required scopes

- `policies:read` for policy/template list and detail.
- `verifications:create` for verification creation, cancellation, and link resend.
- `verifications:read` for verification list, detail, and evidence report URLs.

API-client-created verifications must include an active `policyId`.
