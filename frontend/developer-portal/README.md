# IdentityCore developer portal

Integration documentation application served on `http://localhost:3003`.

```bash
cd frontend
corepack pnpm install --frozen-lockfile
pnpm dev:docs
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` for the displayed REST base URL,
`NEXT_PUBLIC_API_ORIGIN=http://localhost:8000` for interactive API requests, and
`NEXT_PUBLIC_MARKETING_URL=http://localhost:3001` for the marketing-site link. Because
`NEXT_PUBLIC_*` values are embedded in browser bundles, never put API client secrets in
them. `IDENTITYCORE_API_KEY` and `IDENTITYCORE_CLIENT_ID` shown in code samples are
reader-supplied placeholders, not portal runtime credentials. Validate with `pnpm --filter developer-portal lint` and
`pnpm --filter developer-portal build` from `frontend/`.

See the [frontend workspace guide](../README.md) for shared-package and lockfile rules.
