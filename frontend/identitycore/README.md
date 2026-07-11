# IdentityCore Home

Public landing, registration, authentication, password recovery, email verification, and organization-onboarding application at port `3001`. This application remains separate from the authenticated dashboard.

```env
NEXT_PUBLIC_API_ORIGIN=http://localhost:8000
NEXT_PUBLIC_DASHBOARD_URL=http://localhost:3000
NEXT_PUBLIC_DOCS_URL=http://localhost:3003
NEXT_PUBLIC_VERIFICATION_URL=http://localhost:3002
```

Use `pnpm --filter identitycore-web lint` and `pnpm --filter identitycore-web build` for validation.
