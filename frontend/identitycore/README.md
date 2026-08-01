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

Use `pnpm --filter identitycore-web lint` and `pnpm --filter identitycore-web build` for validation.

See [COMPLETION.md](COMPLETION.md) for the audited completion boundary, missing API
contracts, prioritized frontend work, and production release gates.

## Production requirements

- Set every public URL explicitly; `NEXT_PUBLIC_API_ORIGIN` must be an HTTPS origin in production.
- Legacy account and onboarding paths redirect to `NEXT_PUBLIC_DASHBOARD_URL`.
- Set `NEXT_PUBLIC_ALLOW_INDEXING=true` only for the canonical production deployment.
- Configure the backend refresh cookie, CORS allowlist, and object-storage CORS for the deployed web origin.
- Do not place API-client secrets in this application. It authenticates platform users only.
- Verify password-reset and email-verification links use the deployed IdentityCore origin.
- Run `pnpm --filter identitycore-web lint` and `pnpm --filter identitycore-web build` before deployment.
