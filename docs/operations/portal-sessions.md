# Verification BFF session isolation

The browser sends a public `X-Session-Id` selector on every authenticated BFF request.
The server derives a stable SHA-256 cookie-name suffix from that identifier and reads
only that session's HttpOnly bearer cookie. An identifier is never authentication.
The upstream request uses the cookie's bearer and the same session ID; mismatching
URL/session selectors fail before forwarding. Session and upload routes retain their
existing allowlist, origin checks, bounded bodies and request metadata signatures.

Opening another verification link or completing/clearing one flow must not overwrite
or delete another tab's credential. Mobile handoff writes the redeemed session's
scoped cookie before returning its public ID, without returning the bearer. Cookies
remain host-only, Secure in production, SameSite=Strict and path=/; production uses
the __Host- prefix. Encoded token values are bounded so a successful exchange cannot
claim to store a credential exceeding normal per-cookie browser limits.

Fragments remain until the exchange confirms success. Failed network/HTTP or invalid
success envelopes retain the secure link for reload; the error view has a Retry
secure session action. Duplicate initialization shares the in-flight exchange. The
fragment and temporary in-memory bearer are cleared after success; browser local
and session storage never hold the bearer. Do not log URLs, fragments or cookies.

The old two portal-wide cookies are retired; there is no fallback to them. A normal
exchange or handoff expires them. Coordinate the portal cutover and have legacy tabs
reopen their original secure links; sessions whose original link is no longer
available require a replacement link from the requesting organization. Django still
enforces session expiry, tenant ownership, action scopes and consent.

Verify two tabs in one browser context through the actual BFF: exchange both, read
both, clear the first, confirm its access ends and the second still works. Also
rehearse a transient exchange error and successful reload without losing the fragment.
The standalone TLS test runs these checks in Chromium and WebKit.

Production CSP remains nonce-based with no unsafe eval or inline script allowance.
Development alone permits eval for Turbopack hot reload. Hashed Next assets are excluded
from page no-store headers. Evidence uploads intentionally use the consent-aware API
transfer endpoint; the API does not issue session presigned PUT URLs, so external
object-storage origins are not required in connect-src.

Handoff response decoding shares the ten-second upstream deadline and a 16 KiB
response limit. Receiving headers does not end that deadline. The standalone fault
case deliberately stalls after headers and must receive a controlled unavailable
response before the body completes.
