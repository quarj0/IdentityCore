# IdentityCore Frontends

The workspace contains five Next.js applications:

- `dashboard` (`3000`): authenticated organization operations.
- `identitycore` (`3001`): public marketing site; account and onboarding entry points route to the dashboard.
- `verification-portal` (`3002`): subject verification sessions.
- `developer-portal` (`3003`): integration documentation.
- `platform-admin` (`3004`): internal platform administration.

Shared UI and API code live under `packages/`. The dashboard, public site,
developer portal, and platform-admin app use `NEXT_PUBLIC_API_ORIGIN` for Django.
The verification portal deliberately uses the server-only `API_ORIGIN` through its BFF;
it must not expose the Django origin to browser code. App-specific public URL variables
handle cross-application navigation.

Each application README documents its complete runtime variables and production rules.
The verification portal also provides a checked-in `.env.example`; copy values into the
individual application's `.env.local`, never into a browser-visible shared secrets file.

Install the complete frontend workspace from this directory with the pinned package manager:

```bash
corepack pnpm install --frozen-lockfile
```

`frontend/pnpm-lock.yaml` is the sole dependency lockfile for all frontend applications and shared packages. Do not create or use app-local lockfiles; run package commands from this directory so workspace dependency resolution remains reproducible.

Use each package's `lint` and `build` scripts for validation.

## Dashboard CSP resource configuration

Pass these server environment values to the dashboard process (or its `.env.local`
for development). `PUBLIC_ASSET_URL_BASE` automatically allows that origin for images.
`FRONTEND_ASSET_ORIGINS` adds comma-separated approved image/CDN origins, while
`FRONTEND_UPLOAD_ORIGINS` adds the exact origins returned by branding presigned PUT
URLs, including bucket-specific hosts. Paths normalize to origins; wildcard,
credential-bearing and malformed values are ignored. Resource origins require HTTPS
in production; explicit HTTP origins are permitted only during development.

These settings are server configuration, so restart the dashboard after changing
them. They do not allow arbitrary HTTPS sources or relax nonce/inline-style rules.
The verification portal retains its separate image policy and uses consent-aware
same-origin evidence transfers; it does not need external object-storage connect
permission for the current upload contract.

From the frontend workspace, run `pnpm --filter dashboard test:csp` for allowlist
units and `pnpm --filter verification-portal test:e2e:dashboard:csp` for production
Chromium/WebKit checks. The browser fixture verifies nonce-bearing HTML, hydration,
40% native onboarding progress, approved image/PUT requests and blocked unlisted
connections. Portal header coverage also checks script nonce equality and a hydrated
theme change under its enforced policy. No test disables CSP.

Dashboard deployments must set `NEXT_PUBLIC_DASHBOARD_URL` to their public HTTPS
origin at build time; sign-in redirects use this compiled value. Local development
uses `http://localhost:3000`. Rebuild after changes; see [dashboard configuration](dashboard/README.md).
