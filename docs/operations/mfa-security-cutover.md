# MFA authentication security cutover

Password login returns HTTP 202 and an MFA transaction when the account requires enrollment or verification. Use `/api/v1/auth/mfa/enroll` to obtain a setup key, then `/auth/mfa/enroll/confirm` with the transaction and authenticator code. Existing factors use `/auth/mfa/challenge`; an unused recovery code is also accepted. Enrollment confirmation returns ten recovery codes once. The dashboard and Platform Admin display them before continuing. Proofs, setup keys and recovery codes remain in component memory, never browser storage or logs.

Authenticator steps and recovery codes are consumed once under the user lock. A just-used enrollment code cannot be reused to log in: wait for the next authenticator code. Password changes and session revocation invalidate outstanding transactions. Invalid proofs are throttled by the trusted peer address; password-verified proofs share an account bucket across transactions.

## Deploying the format change

This release changes signed transaction and recovery digest formats. Schedule an authentication cutover; the expand-only rolling migration gate deliberately refuses the data migration. Stop new password logins and drain old authentication instances, apply accounts migration `0009`, then enable only the updated authentication instances. Verification processing jobs can continue with their existing contracts. Outstanding transactions from older instances must restart password login.

Migration 0009 converts legacy recovery digests using a conditional update for every row and commits incrementally. It is safe to rerun after interruption. It does not recover or expose plaintext codes. Existing recovery codes remain usable after conversion; newly generated codes contain 128 random bits. Authentication also defensively converts remaining legacy rows.

`MFA_RECOVERY_PEPPER` may specify a dedicated high-entropy secret of at least 32 characters. Its default is the Django secret key with purpose separation. Retain the same key across instances. To rotate, deploy the new primary pepper and provide old peppers in the JSON string array `MFA_RECOVERY_PEPPER_FALLBACKS`. Keep fallbacks until affected users regenerate their recovery codes. Stored MACs cannot be rekeyed without the plaintext code. Changing Django's secret key also changes the default pepper, so retain the old value as a fallback when using that default. Never place key values in command-line arguments, tickets or logs.

Rollback must retain the version-two authentication component and the primary/fallback pepper keys. Do not restore an old binary against protected recovery rows or attempt to reverse the one-way migration. Restore application availability while preserving consumed factors and authentication revocation state.

GraphQL password login and platform-admin invitation acceptance return nullable `tokens` plus `mfaRequired`, `mfaEnrollmentRequired` and `mfaToken` when MFA is required. Complete the REST transaction in the same session scope before using privileged APIs. No access or refresh family is issued by invitation acceptance before the required factor. Legacy enabled flags with neither a TOTP secret nor unused recovery codes enter required enrollment; abandoning setup does not silently remove the requirement.
