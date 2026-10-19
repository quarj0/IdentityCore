# Capture provenance

Upload creation optionally accepts `capture_method`: `camera`, `live_recording`,
`file`, or `unreported` (SDK default). The portal supplies it from the captured File
object and falls back to `file` when its camera is unavailable. Video challenges
still require a live recording or a new one-time handoff to a supported device.

After content validation, the server signs the upload digest and ownership binding
using Django signing with the `identitycore.capture-receipt.v1` salt. The receipt
and its version persist on Upload and follow evidence retention/deletion. No raw
image, biometric attributes, device identifiers, or filenames enter the receipt.
The default signing key and configured fallback keys support deployment rotation;
retain fallback keys while receipts signed by them remain within evidence retention.

Submission rejects missing or altered receipts on version 1 uploads. Version 0
pre-existing uploads remain usable and explicitly unverified only with a signed
legacy enrollment receipt issued by the rollout migration. New uploads default
to version 1; clearing a receipt and changing its version cannot grant legacy
status. The migration enrolls existing rows once in bounded batches. Same-upload retries
preserve their receipt. The risk evidence `capture_provenance` contains bounded
counts only: validated bindings, legacy evidence, invalid receipts, reported sources,
and identical media found in another retained case in this tenant. An invalid receipt
routes existing evidence to manual review unless the existing result is rejection.
Reuse is a review signal, not an identity match or automatic rejection. Counts use
the latest 100 retained uploads; a truncated evidence set routes to manual review
instead of hiding later uploads.

A signed receipt attests what the server validated, not physical camera presence.
Virtual cameras and modified browsers can claim any capture method. Active liveness,
randomized single-use challenges, PAD, and document authenticity retain their own
controls. Neither another case identifier nor its media digest enters the risk report.

Replay lookup uses a composite index on tenant, checksum, status and deletion time
so peer matching does not scan the tenant's complete retained upload history.

Active motion matching uses a bound, ordered eight-direction challenge rather than
unordered membership. See [active liveness](active-liveness.md) for its retry budget,
rollout requirements and evaluation limits.
