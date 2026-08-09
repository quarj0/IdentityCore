# IdentityCore Frontends

The workspace contains five Next.js applications:

- `dashboard` (`3000`): authenticated organization operations.
- `identitycore` (`3001`): public home, auth, and onboarding.
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
