# Generated SDK models

The Python, JavaScript/TypeScript, Java, and .NET SDKs expose models generated
from `docs/openapi/identitycore-public-api.yaml`. Regenerate them after changing
the contract:

```sh
make generate-sdk-models
```

`make check-sdk-models` fails when committed output is stale and also validates
the shared JSON fixtures in `sdk/fixtures` against their source schemas. The
repository-wide test command runs this check before compiling or testing SDKs.

Only data models are generated. Authentication headers, idempotency behavior,
timeouts, retries, response parsing, and webhook verification intentionally
remain in each SDK's hand-written client layer so their behavior can be reviewed
and tested using language-native tools.

Verification listing supports inclusive `created_from` and `created_to` filters
(`YYYY-MM-DD`, deployment time zone). All four SDKs expose them on list and cursor
iteration methods and retain them across pages. See each SDK README for its typed
calling convention. The API returns HTTP 400 for invalid dates or reversed ranges.
