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
exchanges the fragment for a same-origin, session-specific `HttpOnly`, `SameSite=Strict`
cookie. It removes the fragment only after a confirmed successful exchange; failures
retain the link for the Retry secure session action or reload. Duplicate initialization
shares one pending exchange. Browser code never persists or sends
the bearer credential to Django directly; all authenticated requests pass through
the portal BFF.

## Runtime configuration

| Variable                             | Purpose                                                   |
| ------------------------------------ | --------------------------------------------------------- |
| `API_ORIGIN`                         | Required server-only Django API origin used by the BFF.   |
| `VERIFICATION_METADATA_SECRET` | Required production server-only metadata key shared with Django (at least 32 random characters). |
| `VERIFICATION_CLIENT_IP_HEADER` | Optional single-address header overwritten by a trusted ingress; empty means unknown subject IP. |
| `DEPLOYMENT_VERSION`                 | Release identifier returned by the readiness endpoint.    |
| `NEXT_PUBLIC_ONBOARDING_RETURN_URL`  | Optional safe fallback after completion.                  |
| `VERIFICATION_PUBLIC_ORIGIN` | Canonical browser origin, e.g. `https://verify.example.com`. Set this when ingress terminates TLS; it must match the preserved Host header. Paths, credentials and query strings are rejected. |
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

The BFF signs subject metadata rather than forwarding arbitrary browser headers.
See [subject metadata attribution](../../docs/operations/subject-metadata.md) for
ingress trust, rollout, rotation and audit semantics.

## Camera and media compatibility

Live capture requires a secure context and a current browser with `getUserMedia`.
The liveness recorder negotiates MP4/H.264 first for Safari and iOS, then WebM
VP8/VP9 for Chromium-based browsers. Recordings are capped at 15 seconds and
25 MB. Camera streams are stopped when the page is hidden or the capture
component unmounts; an interrupted liveness challenge must be started again so
partial video is never submitted as complete evidence.

Permission denial, camera removal, recorder failure, or an interrupted recording
shows a specific recovery message. Partial video is discarded and an interrupted
challenge is replaced before another capture. A user can retry camera access or
switch to the session's mobile handoff without repeating consent, document, or
selfie steps. A failed live-video submission reuses its known upload and capture
IDs instead of creating another evidence item.

| Browser/device | Automated or manual check | Recovery expectation |
| --- | --- | --- |
| Desktop Chromium over HTTPS | Grant and deny camera permission; retry after denial; disconnect camera during capture | Error is actionable; denied capture creates no upload; interrupted capture is discarded and requires a fresh challenge |
| Desktop WebKit | Verify permission handling and supported recording format | Unsupported recording shows the alternate-device handoff |
| Physical iOS Safari | Check camera permission, app switching, orientation, and MP4 capture | Background interruption discards the partial video; return to the session or continue through a new handoff |
| Physical Android Chrome | Check camera permission, app switching, orientation, and WebM/MP4 capture | Camera disconnection or interruption permits retry with a fresh challenge |
| Insecure context or unsupported browser | Open the session without camera/recorder support | No capture is attempted; user receives browser guidance and an alternate-device option |

Desktop/device emulation checks the interface and deterministic failure paths;
it does not certify camera hardware or physical-device browser behavior. Record
physical iOS and Android results in the pilot release evidence.

## Checks

```bash
pnpm --filter verification-portal lint
pnpm --filter verification-portal build
pnpm test:e2e:verify:install
pnpm test:e2e:verify
```

The browser matrix runs desktop Chromium and WebKit plus Pixel and iPhone device
profiles. Current tests cover subject journeys, keyboard/axe checks, camera recovery, locales,
expiry and security headers. The original IC-081 through IC-086 issues are closed;
ongoing historical review findings remain tracked separately in #281. Real standalone
HTTP/browser transport checks exercise the BFF with a strict TLS upstream fixture. Physical-device certification remains a
release evidence gate because an emulator cannot certify camera hardware.
Provider, storage, worker, and Django integration tests live in their owning
backend applications.

## Policy, consent, and localization

The Django session response is authoritative for the ordered workflow and its
`passive` or `active` liveness mode. The portal does not allow the subject to
select a weaker liveness mode. Consent is rendered from a server-selected,
locale-specific immutable artifact; acceptance echoes its template ID, version,
locale, and SHA-256 digest, and the backend rejects stale artifacts.

English and Arabic are the initial locale architecture baseline. The document language
and direction follow locale negotiation and are updated to the session-selected locale.
The shared shell, skip link, theme controls, known document-retry messages and
root/missing/render-error pages use that locale. Organization/provider content
retains its supplied language; see the [locale contract](../../docs/architecture/applicant-localization.md).
Legacy outcome URL suffixes load authenticated session state instead of asserting an outcome.
IC-083 is closed with repository locale/fallback/RTL acceptance coverage; later review
findings still require individual disposition. Production locale
support also requires the physical-device evidence described in
`docs/operations/verification-portal-production.md`.

## Production image

Build the standalone non-root image with the frontend directory as context:

```bash
docker build -f verification-portal/Dockerfile \
  --build-arg NEXT_PUBLIC_ONBOARDING_RETURN_URL=https://dashboard.example.com/onboarding \
  --build-arg NEXT_PUBLIC_ALLOWED_RETURN_ORIGINS=https://dashboard.example.com \
  -t identitycore/verification-portal .
```

The two `NEXT_PUBLIC_` return values are public build inputs embedded in browser
code; changing only the runtime container environment cannot update them. Rebuild
the image when they change. API_ORIGIN and metadata keys remain server-only runtime
configuration; never pass secrets through public build arguments.

The runtime exposes `/api/health` for process liveness and `/api/ready` for
runtime-configuration readiness. Dependency availability is monitored separately
so a provider or Django incident does not create a container restart loop.

## Maturity status

The portal is a working repository vertical slice; IC-081 through IC-086 are closed.
Later historical findings remain open in #281. `COMPLETION.md` distinguishes those repository-owned gaps from the
additional deployment, independent-assurance, provider, physical-device, pilot, and
approval gates.

Active capture uses an initial neutral hold followed by eight ordered prompts in
about 20 seconds. The server binds provider evidence to the issued challenge and
caps retries across sessions. See [active-liveness operations](../../docs/operations/active-liveness.md)
for provider compatibility, rollout and physical-device evaluation limits.

Each BFF request selects its session with `X-Session-Id`; this public identifier is
not a credential. The server reads only that session's hashed-name bearer cookie.
Clearing one flow leaves other tabs intact. Old portal-wide cookies are retired
and removed during exchange/handoff; deployments must ask already-open legacy tabs
to reopen their secure link. See [BFF session operations](../../docs/operations/portal-sessions.md).

Development CSP permits eval for Turbopack hot reload. Production retains nonce-based
scripts and forbids unsafe eval/inline scripts. Session evidence uses the consent-aware
BFF transfer path; self-only connect-src does not require object-storage origin access.

The default Playwright acceptance suite starts its own production build on port 3002
and does not reuse development servers. Stop a development server on that port
before running it; strict production CSP and release-version assertions remain active.

The HTML proxy forwards the exact nonce-bearing CSP to Next's renderer and returns
that same policy to the browser. Production header tests check the initial framework
script nonces and a hydrated theme toggle, rather than checking response headers
alone. The portal's same-origin evidence transfer contract is documented in the
[session guide](../../docs/operations/portal-sessions.md).

The [accessibility validation procedure](../../docs/operations/accessibility-validation.md)
describes the consolidated English/Arabic keyboard/touch journeys, mounted capture
and recording scans, QR handoff, terminal outcomes and reviewer supporting-evidence
scenario. Axe uses the production response nonce; the checks keep CSP enforced.
Automated browser profiles do not replace physical-device or assistive-technology
assessment.

The Dockerfile-specific ignore file excludes local dependencies, build/test outputs
and environment files from the build context. The image installs dependencies from
the frozen lockfile; local browser-test artifacts must not replace container output.
