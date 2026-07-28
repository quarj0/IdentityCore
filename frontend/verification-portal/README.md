# IdentityCore Verification Portal

The verification portal is the subject-facing Next.js application for consent,
identity-document capture, selfie and active-liveness capture, processing status,
and desktop-to-mobile handoff. It runs on port `3002` locally.

## Local development

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

The Django API must be available at `NEXT_PUBLIC_API_ORIGIN`. Verification links
have the form `/verify/{session_id}#token={session_token}`. The portal
removes the fragment from browser history and never sends it in a referrer.

## Runtime configuration

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_ORIGIN` | Browser-visible Django API origin. |
| `NEXT_PUBLIC_ONBOARDING_RETURN_URL` | Optional safe fallback after completion. |
| `NEXT_PUBLIC_ALLOWED_RETURN_ORIGINS` | Comma-separated allowlist of organization return origins. |

Production return URLs must use HTTPS and must match the portal origin or an
origin in `NEXT_PUBLIC_ALLOWED_RETURN_ORIGINS`. Local HTTP origins are accepted
only outside production. Invalid organization redirects fall back safely to the
configured return URL or the portal origin.

## Security model

Every route sends a no-store cache policy, a restrictive Content Security Policy,
clickjacking protection, a no-referrer policy, MIME-sniffing protection, and a
Permissions Policy that limits camera access to this origin. The API origin is
the only external connection target admitted by the portal CSP. Organization
logos are limited to HTTPS outside local development.

TLS and `Strict-Transport-Security` must be enforced at the production ingress.
Only explicitly trusted portal origins should be present in Django's CORS
configuration.

## Camera and media compatibility

Live capture requires a secure context and a current browser with `getUserMedia`.
The liveness recorder negotiates MP4/H.264 first for Safari and iOS, then WebM
VP8/VP9 for Chromium-based browsers. Recordings are capped at 15 seconds and
25 MB. Camera streams are stopped when the page is hidden or the capture
component unmounts; an interrupted liveness challenge must be started again so
partial video is never submitted as complete evidence.

## Checks

```bash
pnpm lint
pnpm build
pnpm exec playwright install chromium
pnpm test:e2e
```

The browser suite covers the primary subject flow, expiry handling, and response
security headers. Provider, storage, worker, and Django integration tests live in
their owning backend applications.
