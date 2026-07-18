# IdentityCore Home

Public landing, registration, authentication, password recovery, email verification, and organization-onboarding application at port `3001`. This application remains separate from the authenticated dashboard.

```env
NEXT_PUBLIC_API_ORIGIN=http://localhost:8000
NEXT_PUBLIC_DASHBOARD_URL=http://localhost:3000
NEXT_PUBLIC_DOCS_URL=http://localhost:3003
NEXT_PUBLIC_VERIFICATION_URL=http://localhost:3002
```

Use `pnpm --filter identitycore-web lint` and `pnpm --filter identitycore-web build` for validation.

## Production requirements

- Set every public URL explicitly; `NEXT_PUBLIC_API_ORIGIN` must be an HTTPS origin in production.
- Configure the backend refresh cookie, CORS allowlist, and object-storage CORS for the deployed web origin.
- Do not place API-client secrets in this application. It authenticates platform users only.
- Verify password-reset and email-verification links use the deployed IdentityCore origin.
- Run `pnpm --filter identitycore-web lint` and `pnpm --filter identitycore-web build` before deployment.
