# Tenant branding and accessibility

Tenant branding is selected from the verification project's environment. Sandbox and production each have an independent draft and published version. An unpublished draft does not change applicant sessions; publishing changes only the selected environment.

Branding uploads accept PNG, JPEG, and WebP assets up to 5 MiB. The declared MIME type must match the filename extension. SVG uploads are rejected so tenant-provided active markup cannot be rendered in the applicant portal. Uploads are stored in the organization's branding keyspace.

The publishing API checks WCAG AA contrast for button text against the primary color and standard applicant text against the configured background. Both ratios must be at least 4.5:1. The dashboard preview reports the measured ratios and blocks publishing when either check fails. This check covers the configured text combinations; operators should still check full pages, focus indicators, logo legibility, and localized layouts before production rollout.

## Pilot checks

- Verify the sandbox project displays the sandbox published version.
- Verify production continues to display its own published version after sandbox edits or publish.
- Upload a raster logo and confirm it appears in preview; confirm SVG and files over 5 MiB are rejected.
- Check the displayed contrast ratios and attempt publishing with a failing palette to confirm the server rejects it.
- Review keyboard focus, screen reader names, zoom/reflow, and RTL layout for each supported language before production.
