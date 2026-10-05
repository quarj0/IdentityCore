# Tenant and environment object routing

Install the expand-only `tenants.0006` migration before deploying this code. Configure the existing S3-compatible endpoint, credentials and media/temp/evidence bucket settings. Tenant routes use that approved endpoint and identity; tenants cannot supply endpoints or credentials.

Set `TENANT_STORAGE_DESTINATIONS` to a JSON object mapping approved bucket names to their verified residency region, for example `{"approved-eu-bucket":"eu-west-1"}`. The deployment operator must verify actual bucket region, access policy, encryption, retention and processor safeguards; this allowlist records the approved destination and does not infer cloud configuration. Grant the application and internal AI identity only required object operations in the approved buckets and tenant prefixes. Prefer separate tenant/environment buckets when cloud access policy requires physical separation.

Authorized deployment operators provision a route:

```sh
python backend/django/manage.py configure_tenant_storage --tenant "$TENANT_PUBLIC_ID" --environment sandbox --bucket approved-eu-bucket --residency-region eu-west-1
```

The command records an audit event and prints only route ID, environment and region. New upload and evidence keys include tenant, environment and immutable route ID. S3 object metadata and internal transfer references retain route and residency information. AI/provider requests contain object references and required attributes; they do not embed applicant evidence bytes. Upload grants permit one PUT with declared type and size and expire within ten minutes and before the upload expires. Download grants permit one GET and expire within five minutes. Routed grants fail closed when S3 is unavailable; no unsigned fallback is issued.

Provisioning a replacement affects new objects only. Existing keys keep their original bucket and region for reading, rotation, deletion and backup. Retain routes, approved destinations and access to old buckets until all objects and recovery requirements are satisfied. Route records cannot be edited or removed through their model interface. With a configured route but no usable active route, new keys fail closed. Unconfigured tenants and legacy keys continue using the existing buckets; provisioning does not migrate old objects or change their residency. Plan any legacy relocation separately with deletion verification.

Backups include every retained route bucket and verify required references against their actual destination. An isolated restore must use distinct empty buckets, preserving bucket aliases and residency. Set `TENANT_STORAGE_BUCKET_REMAP` to a trusted JSON mapping of each source route bucket to its approved empty restore bucket, and include the targets with their original region in `TENANT_STORAGE_DESTINATIONS`. Restore targets must exactly match the source route roles in the authenticated backup manifest. The restore object phase uses only validated target buckets before importing the database. Retain the remap in the restored deployment so immutable route references resolve to the recovered objects. Changing region through the remap is rejected. Test the complete restore drill before enabling a recovered tenant.
