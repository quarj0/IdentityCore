# ADR-014: Make upload completion idempotent

## Status

Accepted

## Decision

An upload remains `initiated` until the server receives and validates the
content. Successful transfer records the upload as `uploaded` and stores its
SHA-256 checksum. The upload row is locked during short state transitions; media and storage I/O
run outside SQL. [ADR 057](ADR-057-upload-transfer-transactions.md) defines
concurrent candidates, fresh-consent acceptance and cleanup limitations.

Repeating completion with the same size, MIME type, and checksum returns the
same successful result without writing storage again. Repeating it with
different content is rejected. Evidence submission later moves the upload to
`consumed`, preserving a single processing chain for each upload.
