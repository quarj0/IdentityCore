# ADR-038: One-time mobile handoff capabilities

Status: Accepted

A handoff capability belongs to one source session and never substitutes a bearer
in a URL. Fragment-only transport keeps claims out of HTTP requests and server
props. The client clears the fragment before redemption and binds the request to
the source session in the scanned URL. The BFF stores the fresh returned bearer
in an HttpOnly cookie and strips it from the browser payload.

Creation and redemption acquire the tenant audit lock before source-session and
handoff locks. Current source scope, expiry, case state and tenant status are
validated under the transaction. Reissuing a QR invalidates pending capabilities;
one-time consumption is serialized on PostgreSQL. The desktop remains able to
poll progress with its original cookie without sharing its bearer with the phone.
The public redemption request now requires its source session identifier, and
legacy query links must be regenerated as a fragment-only QR.
