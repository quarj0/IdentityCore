# IdentityCore Verification Portal

The verification portal is the subject-facing Next.js application for consent,
identity-document capture, selfie and active-liveness capture, processing status,
and desktop-to-mobile handoff. It runs on port `3002` locally.

## Local development

```bash
cd frontend
corepack pnpm install --frozen-lockfile
cp verification-portal/.env.example verification-portal/.env.local
pnpm dev:verify
```

The Django API must be available at the server-only `API_ORIGIN`.
Browser-visible API origins are intentionally unsupported. Verification links
have the form `/verify/{session_id}#token={session_token}`. The portal
immediately exchanges the fragment for a same-origin, `HttpOnly`, `SameSite=Strict`
cookie and removes it from browser history. Browser code never persists or sends
the bearer credential to Django directly; all authenticated requests pass through
the portal BFF.

## Runtime configuration

| Variable                             | Purpose                                                   |
| ------------------------------------ | --------------------------------------------------------- |
| `API_ORIGIN`                         | Required server-only Django API origin used by the BFF.   |
| `DEPLOYMENT_VERSION`                 | Release identifier returned by the readiness endpoint.    |
| `NEXT_PUBLIC_ONBOARDING_RETURN_URL`  | Optional safe fallback after completion.                  |
| `NEXT_PUBLIC_ALLOWED_RETURN_ORIGINS` | Comma-separated allowlist of organization return origins. |

Production return URLs must use HTTPS and must match the portal origin or an
origin in `NEXT_PUBLIC_ALLOWED_RETURN_ORIGINS`. Local HTTP origins are accepted
only outside production. Invalid organization redirects fall back safely to the
configured return URL or the portal origin.

## Security model

Every route sends a no-store cache policy, a restrictive Content Security Policy,
clickjacking protection, a no-referrer policy, MIME-sniffing protection, and a
Permissions Policy that limits camera access to this origin. Authenticated browser connections are restricted to the same-origin BFF.
Organization logos are limited to HTTPS outside local development.

Production refuses an absent, invalid, credential-bearing, path-bearing, or
non-HTTPS `API_ORIGIN`. TLS and `Strict-Transport-Security` must be enforced at
the production ingress.
The browser does not require Django CORS access. Mutating BFF routes reject
cross-origin requests in addition to the strict cookie policy.

## Camera and media compatibility

Live capture requires a secure context and a current browser with `getUserMedia`.
The liveness recorder negotiates MP4/H.264 first for Safari and iOS, then WebM
VP8/VP9 for Chromium-based browsers. Recordings are capped at 15 seconds and
25 MB. Camera streams are stopped when the page is hidden or the capture
component unmounts; an interrupted liveness challenge must be started again so
partial video is never submitted as complete evidence.

## Checks

```bash
pnpm --filter verification-portal lint
pnpm --filter verification-portal build
pnpm test:e2e:verify:install
pnpm test:e2e:verify
```

The browser matrix runs desktop Chromium and WebKit plus Pixel and iPhone device
profiles. It covers the primary subject flow, keyboard interaction, expiry
handling, and response security headers. Physical-device certification remains
a release evidence gate because an emulator cannot certify camera hardware.
Provider, storage, worker, and Django integration tests live in their owning
backend applications.

## Policy, consent, and localization

The Django session response is authoritative for the ordered workflow and its
`passive` or `active` liveness mode. The portal does not allow the subject to
select a weaker liveness mode. Consent is rendered from a server-selected,
locale-specific immutable artifact; acceptance echoes its template ID, version,
locale, and SHA-256 digest, and the backend rejects stale artifacts.

English and Arabic are the initial locale architecture baseline. The document
language and direction follow locale negotiation and are updated to the
session-selected locale. New production locales must add a complete catalog and
pass the RTL, keyboard, axe, WebKit, and physical-device evidence gates described
in `docs/operations/verification-portal-production.md`.

## Production image

Build the standalone non-root image with the frontend directory as context:

```bash
docker build -f verification-portal/Dockerfile -t identitycore/verification-portal .
```

The runtime exposes `/api/health` for process liveness and `/api/ready` for
runtime-configuration readiness. Dependency availability is monitored separately
so a provider or Django incident does not create a container restart loop.

## Completion status

The repository-owned implementation is complete. The remaining release gates
require deployment owners, independent assessors, providers, or physical-device
testers and are tracked separately in `COMPLETION.md`; they are not represented as
unfinished portal code.
