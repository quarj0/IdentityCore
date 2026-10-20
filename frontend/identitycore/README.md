# IdentityCore Home

Public marketing application at port `3001`. Registration, authentication, password
recovery, email verification, and organization onboarding are owned by the dashboard.

```env
NEXT_PUBLIC_API_ORIGIN=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3001
NEXT_PUBLIC_DASHBOARD_URL=http://localhost:3000
NEXT_PUBLIC_DOCS_URL=http://localhost:3003
NEXT_PUBLIC_VERIFICATION_URL=http://localhost:3002
NEXT_PUBLIC_ALLOW_INDEXING=false
```

From `frontend/`, run `corepack pnpm install --frozen-lockfile` and then
`pnpm dev:web`; open `http://localhost:3001`.

Use `pnpm --filter identitycore-web lint` and `pnpm --filter identitycore-web build` for validation.

See [COMPLETION.md](COMPLETION.md) for current application ownership, validation and
release boundaries.

## Production requirements

- Set every public URL explicitly; `NEXT_PUBLIC_API_ORIGIN` must be an HTTPS origin in production.
- Legacy account and onboarding paths redirect to `NEXT_PUBLIC_DASHBOARD_URL`.
- Set `NEXT_PUBLIC_ALLOW_INDEXING=true` only for the canonical production deployment.
- Configure CORS for public catalog/contact calls. Dashboard account cookies and evidence uploads use the dashboard origin.
- Do not place API-client or server secrets in this public application.
- Verify account and onboarding redirects reach the configured dashboard origin.
- Run `pnpm --filter identitycore-web lint` and `pnpm --filter identitycore-web build` before deployment.
