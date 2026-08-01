# IdentityCore Dashboard

Organization account and workspace application at port `3000`. It owns registration,
email verification, sign-in, onboarding, projects, workflows, verification requests,
subjects, manual review, API clients, webhooks, audit events, team access, and settings
through the Django API.

Required configuration:

```env
NEXT_PUBLIC_API_ORIGIN=http://localhost:8000
NEXT_PUBLIC_IDENTITYCORE_ORIGIN=http://localhost:3001
```

The public IdentityCore frontend sends all account actions to this application. Use
`pnpm --filter dashboard lint`, `pnpm --filter dashboard test`, and
`pnpm --filter dashboard build` for validation. Development servers are started only
when explicitly requested.
