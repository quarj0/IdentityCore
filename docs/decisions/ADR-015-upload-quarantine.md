# ADR-015: Quarantine untrusted upload content

## Status

Accepted

## Decision

Upload completion validates bytes against the declared media type before the
object is written to temporary storage. Supported images are decoded and
verified with Pillow; supported video containers are checked for their
container signatures; the standard antivirus test signature is rejected.

Unrecognized or unsafe content is recorded as `quarantined` with a bounded
reason code and is never eligible for document, selfie, or liveness
processing. Production deployments must pair this gate with their managed
malware-scanning control for full AV coverage.
