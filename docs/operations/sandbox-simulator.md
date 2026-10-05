# Deterministic sandbox scenarios

Create a normal verification with an active sandbox project and sandbox policy. Before collecting consent or media, POST to `/api/v1/verifications/{verification_id}/simulate` using the same tenant's authenticated user or sandbox API-client credentials with `verifications:create`. API clients remain limited to their credential's environment. The command accepts:

```json
{"scenario": "approved"}
```

| Scenario | Result status | Decision reason | Provider status |
| --- | --- | --- | --- |
| approved | verified | risk_rules_approved | completed |
| declined | rejected | risk_rules_rejected | completed |
| review | manual_review_required | risk_rules_review | completed |
| timeout | failed | provider_timeout | timeout |
| provider_error | failed | provider_unavailable | failed |

The response is the ordinary version-one verification result, with `simulation` containing `scenario` and `version: 1`. GET `/verifications/{id}/result` returns the same contract. Provider provenance names `sandbox-simulator-v1` and model `sandbox-simulator` version `1`; artificial check duration is zero. Identifiers and timestamps remain normal per-case values, while outcome behavior is fixed.

Terminal/review events use the standard webhook envelope and `verification.verified`, `verification.rejected`, `verification.manual_review_required` or `verification.failed` event types. Their data contains the same simulation marker. Only sandbox endpoints receive these events; production endpoints are excluded. No real provider, AI, media or identity processing occurs. Capture sessions are revoked and cannot be renewed for synthetic cases.

Use a separate pristine case for each scenario. Repeating the same command returns its existing result without a second decision or webhook event; selecting a different scenario for that case fails validation. Existing consent, media, jobs, provider checks or decisions make the command ineligible. Suspended/deleted tenants, inactive projects, platform-owned review cases and all production projects are denied. DEBUG, custom headers, metadata or particular applicant names cannot enable production simulation or forge the server-owned marker.

For example, after obtaining the normal create-response verification ID:

```sh
curl --fail-with-body "$API_ORIGIN/api/v1/verifications/$VERIFICATION_ID/simulate" \
  -H "X-Client-Id: $SANDBOX_CLIENT_ID" \
  -H "Authorization: Bearer $SANDBOX_CLIENT_SECRET" \
  -H 'Content-Type: application/json' \
  --data '{"scenario":"timeout"}'
```

Read credentials from your existing secret manager. The simulator does not provision credentials or promote workspaces. Never use actual applicant data in synthetic demonstrations. Audit entries record only fixed scenario/version and case identifiers. The separate simulation table is an additive migration and does not rewrite existing case data.
