# IdentityCore Frontends

The workspace contains five Next.js applications:

- `dashboard` (`3000`): authenticated organization operations.
- `identitycore` (`3001`): public home, auth, and onboarding.
- `verification-portal` (`3002`): subject verification sessions.
- `developer-portal` (`3003`): integration documentation.
- `platform-admin` (`3004`): internal platform administration.

Shared UI and API code live under `packages/`. All applications use `NEXT_PUBLIC_API_ORIGIN` for Django and app-specific public URL variables for cross-application navigation.

Install the complete frontend workspace from this directory with the pinned package manager:

```bash
corepack pnpm install --frozen-lockfile
```

`frontend/pnpm-lock.yaml` is the sole dependency lockfile for all frontend applications and shared packages. Do not create or use app-local lockfiles; run package commands from this directory so workspace dependency resolution remains reproducible.

Use each package's `lint` and `build` scripts for validation.
