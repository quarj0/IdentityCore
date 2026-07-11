# IdentityCore Frontends

The workspace contains five Next.js applications:

- `dashboard` (`3000`): authenticated organization operations.
- `identitycore` (`3001`): public home, auth, and onboarding.
- `verification-portal` (`3002`): subject verification sessions.
- `developer-portal` (`3003`): integration documentation.
- `platform-admin` (`3004`): internal platform administration.

Shared UI and API code live under `packages/`. All applications use `NEXT_PUBLIC_API_ORIGIN` for Django and app-specific public URL variables for cross-application navigation. Install from this directory with `pnpm install`; use each package's `lint` and `build` scripts for validation.
