# Private vulnerability intake

GitHub private vulnerability reporting is enabled, verified by repository API on
2026-10-20 after administrator activation. The concrete
channel is [GitHub private reporting](https://github.com/quarj0/IdentityCore/security/advisories/new).
Possible and confirmed vulnerabilities must not be collected through public forms.
The public security-hardening form is only for preventive work without vulnerability
details; bug, feature, test and documentation forms carry the same private-channel
warning.

## Administrator activation

Enable private vulnerability reporting from the repository's Security/Advisories
controls, then verify with an appropriately authorized account:

```sh
gh api repos/quarj0/IdentityCore/private-vulnerability-reporting
```

The response must report `enabled: true`. Confirm an ordinary signed-in reporter
can open the private intake flow. Do not submit a sample report or notify maintainers
merely to validate navigation. Public issue forms cannot make sensitive disclosure
safe; reporters must choose the private channel before entering details.

On 2026-10-19, the repository was public and private reporting returned
`enabled: false`. The connected integration's enable request returned HTTP 403,
`Resource not accessible by integration`, despite reported repository admin access.
The administrator subsequently enabled reporting on 2026-10-20; the same API now
returns `enabled: true`. The disabled-setting blocker is cleared. An ordinary
signed-in reporter should still verify intake navigation before release; that
manual account-role check was not performed by this integration.

The typed public forms cover every advertised backlog work type and use existing
`type:bug`, `type:feature`, `type:security`, `type:test`, `type:docs` labels. Maintainers
may create sanitized remediation work after private triage; this is not permission
to copy private reports into public issues.
