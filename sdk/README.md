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
