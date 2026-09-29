# Applicant locale behavior

The hosted verification portal negotiates an initial locale from the request's `Accept-Language` preference, matched against the tenant policy's configured locales. The applicant can change the language before continuing; the portal requests session content again using the selected locale and stores the preference only for that browser verification session. Unsupported language tags fall back to a configured supported locale, then English.

The current portal UI dictionaries support English (`en`) and Arabic (`ar`). Arabic uses right-to-left document direction. Consent text is returned by the backend using the same selected locale as the session. The consent acceptance request sends the consent template ID, version, locale, and content hash; the resulting consent record stores that locale and immutable version. Changing the UI language after consent does not rewrite an existing consent record.

Date and number display uses `Intl.DateTimeFormat` and `Intl.NumberFormat` with the resolved locale. Any unsupported locale uses the English fallback. When adding a locale, add its complete applicant-facing dictionary, configure it on the verification policy and consent template, and run the browser test for locale negotiation, consent locale persistence, formatting, and text direction.
