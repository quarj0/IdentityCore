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

From `frontend/`, run `corepack pnpm install --frozen-lockfile` and then
`pnpm dev:dashboard`; open `http://localhost:3000`.

The public IdentityCore frontend sends all account actions to this application. Use
`pnpm --filter dashboard lint`, `pnpm --filter dashboard test`, and
`pnpm --filter dashboard build` for validation. Development servers are started only
when explicitly requested.

Evidence report downloads use the authenticated API client, including scoped refresh,
and download exact response bytes. Organization PDF transfers allow a 60-second deadline,
normalize a missing browser MIME to `application/pdf`, and retain server content validation.
Replacing submitted documents is detected by storage-key changes rather than file count.

Dashboard image and branding-upload origins are configured by the server-only
`PUBLIC_ASSET_URL_BASE`, `FRONTEND_ASSET_ORIGINS` and `FRONTEND_UPLOAD_ORIGINS`
settings. Configure the actual presigned-upload bucket origins before using branding
uploads. See the [workspace CSP guide](../README.md#dashboard-csp-resource-configuration)
for HTTPS/allowlist rules and production browser checks. Onboarding progress uses
native progress rendering, preserving its numeric/accessibility value without
inline styles.
