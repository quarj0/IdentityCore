# IdentityCore platform administration

Internal operator application served on `http://localhost:3004`. It manages platform
operations through Django's authenticated REST and GraphQL contracts.

```bash
cd frontend
corepack pnpm install --frozen-lockfile
NEXT_PUBLIC_API_ORIGIN=http://localhost:8000 pnpm dev:admin
```

`NEXT_PUBLIC_API_ORIGIN` is the Django origin. Public variables are browser-visible;
never store credentials or provider secrets in them. Validate with
`pnpm --filter platform-admin lint` and `pnpm --filter platform-admin build` from
`frontend/`.

See the [frontend workspace guide](../README.md) for ports, shared packages, and
lockfile rules.

Platform invitations grant full administration and queue encrypted single-use email links.
Configure the HTTPS acceptance URL and deployment email settings as described in
[platform invitation operations](../../docs/operations/platform-invitations.md).
The public `/accept-invitation` page clears fragment credentials and returns recipients
to normal MFA-aware sign-in. Unsupported limited invitation roles are rejected.
