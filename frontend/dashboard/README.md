# IdentityCore Dashboard

Authenticated organization workspace at port `3000`. It manages projects, workflows, verification requests, subjects, manual review, API clients, webhooks, audit events, team access, and settings through the Django API.

Required configuration:

```env
NEXT_PUBLIC_API_ORIGIN=http://localhost:8000
NEXT_PUBLIC_IDENTITYCORE_ORIGIN=http://localhost:3001
```

Use `pnpm --filter dashboard lint` and `pnpm --filter dashboard build` for validation. Development servers are started only when explicitly requested.
