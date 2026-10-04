# Deployed security promotion gate

Run the **Deployment security promotion gate** workflow against the candidate deployment before routing production traffic. It is also a reusable workflow: rollout workflows must depend on its successful `deployment-security` job before promotion. A missing policy, smoke credential, unreachable target, invalid certificate, redirect, or unsafe response fails the gate. This repository does not automatically promote deployments.

Each protected GitHub Environment (`sandbox` or `production`) owns a `DEPLOYMENT_SECURITY_CONFIG` variable:

```json
{
  "environment": "sandbox",
  "api": "https://api.sandbox.example.org",
  "dashboard": "https://dashboard.sandbox.example.org",
  "portal": "https://verify.sandbox.example.org",
  "approved_origins": ["https://dashboard.sandbox.example.org", "https://verify.sandbox.example.org"],
  "refresh_cookie_name": "identitycore_refresh_dashboard"
}
```

Origins must match the deployed API's approved origin list for that environment. No wildcard, credentials, path, query, fragment, or HTTP targets are accepted. The gate tests explicit approved preflights, several unapproved origins including localhost, anonymous private access, disallowed public methods, and the portal's cross-origin session boundary. TLS uses trusted certificates and requires TLS 1.2 or newer. There is no insecure option. Operator-owned private CAs can be supplied locally with `--ca-file`.

Set environment secrets `DEPLOYMENT_SMOKE_EMAIL`, `DEPLOYMENT_SMOKE_PASSWORD`, `DEPLOYMENT_SMOKE_SESSION_ID`, and `DEPLOYMENT_SMOKE_SESSION_TOKEN`. Use an ordinary synthetic account with no sensitive access and an expiring synthetic verification session with read-only actions. Use a dedicated smoke account that does not require MFA; a challenge response fails the cookie probe instead of skipping it. Refresh-cookie issuance uses the dashboard scope and the probe logs out in a `finally` block even if cookie flags are unsafe. Portal cookies are exchanged and cleared; the synthetic verification bearer must expire or be revoked by its fixture owner. The probe never uploads media or changes verification outcomes.

The report contains environment, fixed check names, and pass/fail booleans. It excludes credentials, URLs, cookies, response bodies, raw headers, and exception messages. Preserve this sanitized artifact as promotion evidence. Do not enable shell tracing or upload the policy/credentials as an artifact.

The gate checks one-year HSTS, nosniff, restricted referrer/framing policies, and frontend CSP directives without unsafe script execution. Issued refresh cookies must be host-only, HttpOnly, Secure, SameSite Lax/Strict, and scoped to `/api/v1/auth/`; portal `__Host-` cookies must use `/` and Strict/Lax. Frontend headers should remain present on the public routes used by the gate.

Django production settings redirect HTTP to HTTPS and emit HSTS. If TLS terminates at a proxy, set `DJANGO_TRUST_PROXY_HEADERS=true` **only** when that trusted proxy strips incoming `X-Forwarded-Proto` and replaces it with the observed transport scheme. A direct client must never control this header. Configure HTTPS health checks at the proxy or an explicit trusted transport; repeated redirects fail the gate. Development keeps localhost CORS support; production uses explicit HTTPS origins and rejects localhost/wildcard/non-origin entries. Set `DJANGO_CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS` explicitly for each environment. An empty list permits no browser origins; production never inherits the development lists. Refresh cookies are always Secure in production.

Local validation:

```sh
python -m unittest discover -s scripts -p test_deployed_security.py
python scripts/check_deployed_security.py --config policy.json --output deployment-security-report.json
```

The fixture suite runs a real local HTTPS server with a temporary certificate, verifies trust rejection and unsafe headers/cookies/origins/endpoints, and confirms backend session cleanup after failure. Temporary private keys remain outside the repository. Real sandbox/production promotion requires a fresh report from the deployed candidate; passing fixtures alone does not certify a deployment.
