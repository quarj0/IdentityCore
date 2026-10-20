# Applicant locale behavior

The hosted verification portal negotiates its initial shell locale from the request's weighted `Accept-Language` preference and the supported UI dictionaries. The authenticated session endpoint independently matches that preference against the tenant policy and available frozen consent translations; the flow then adopts the returned locale. The applicant can change the language before continuing; the portal requests session content again using the selected locale and stores the preference only for that browser verification session. Unsupported language tags fall back to a configured supported locale, then English.

The current portal UI dictionaries support English (`en`) and Arabic (`ar`). Arabic uses right-to-left document direction. Consent text is returned by the backend using the same selected locale as the session. The consent acceptance request sends the consent template ID, version, locale, and content hash; the resulting consent record stores that locale and immutable version. Changing the UI language after consent does not rewrite an existing consent record.

Date and number display uses `Intl.DateTimeFormat` and `Intl.NumberFormat` with the resolved locale. Any unsupported locale uses the English fallback. When adding a locale, add its complete applicant-facing dictionary, configure it on the verification policy and consent template, and run the browser test for locale negotiation, consent locale persistence, formatting, and text direction.

The initial locale also reaches the shared portal shell and render-error boundary.
The root and missing-page responses negotiate it from `Accept-Language`; shell
controls follow changes to the document language when the authenticated session
selects a different locale. Theme controls expose translated accessible names.
Controlled consent, capture, liveness, handoff and outcome copy supports both
languages. Country names use `Intl.DisplayNames`; known document and side labels
and the supported backend document-retry message formats use the same dictionary.
Organization names, custom document labels, consent bodies and unknown provider
messages remain supplied content; the portal does not machine-translate them.

Legacy `/verify/{sessionId}/complete`, `/expired` and `/error` paths render the
same authenticated session flow as `/verify/{sessionId}`. A URL suffix is never
evidence that a verification was submitted, expired or failed. The flow derives
its displayed result from authenticated session/status responses.

Validation includes English and Arabic consent-to-result accessibility journeys
in Chromium and WebKit, Arabic root/missing-page and theme controls, anonymous
legacy outcome aliases, language selection/consent persistence, and unit checks
for bounded retry-message translation and country-name fallbacks. Mocked browser
journeys validate presentation and interaction, not provider or biometric accuracy.
