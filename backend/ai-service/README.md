# Internal AI service

FastAPI performs document quality/classification/OCR and biometric checks. It is an
internal service, not a browser-facing API, and requires `X-Internal-Token`.

```bash
cp .env.example .env
docker compose up --build -d ai-service
curl -H "X-Internal-Token: $(sed -n 's/^AI_SERVICE_SHARED_TOKEN=//p' .env)" http://localhost:8001/v1/ready
docker compose run --rm ai-service pytest
```

The service listens on `8001`. `AI_SERVICE_SHARED_TOKEN`, `AI_SERVICE_MODE`, and
`AI_MODEL_ROOT` are required runtime settings. `INSIGHTFACE_MODEL_NAME`,
`INSIGHTFACE_ALLOW_DOWNLOAD`, `PADDLE_OCR_ALLOW_DOWNLOAD`, and the `PAD_*`
settings control model loading. The PAD model is a separately approved ONNX
asset at `AI_MODEL_ROOT/liveness/pad.onnx`; its SHA-256 digest must be included
in the model manifest. Real mode refuses liveness processing when that asset is
missing, invalid, or altered. Fetch the pinned initial candidate with:

```bash
python scripts/fetch_pad_model.py --model-root /opt/identitycore/models
```

When using Compose's model volume, fetch the asset before creating the manifest:

```bash
docker compose --profile model-bootstrap run --rm --entrypoint python \
  ai-model-bootstrap /app/scripts/fetch_pad_model.py \
  --model-root /opt/identitycore/models
docker compose --profile model-bootstrap run --rm ai-model-bootstrap
```

The initial candidate is MiniFASNetV2 2.7_80x80 with a three-logit output
(`print attack`, `live`, `replay attack`), so `PAD_LIVE_CLASS_INDEX` defaults
to `1`. It is a baseline candidate,
not a production performance claim; it must pass our held-out Ghana/device PAD
evaluation before pilot use.

## Country and document coverage

The PAD model is shared across countries. Document classification and capture
requirements are country-specific:

| Country | Enabled document coverage | Status |
| --- | --- | --- |
| Ghana (GH) | National ID, passport | Enabled |
| Nigeria (NG) | Passport | Passport-only |
| Senegal (SN) | Passport | Passport-only |
| Togo (TG) | Passport | Passport-only |
| Côte d’Ivoire (CI) | Passport | Passport-only |

Other country/document combinations remain unsupported and must route to
manual review. Adding a national ID requires an approved fixture set, document
definition, capture-side rules, OCR/MRZ tests where applicable, and a country-
specific evaluation report.
Production images should preload models; bootstrap the named Compose volume explicitly
when downloads are intended:

```bash
docker compose --profile model-bootstrap run --rm ai-model-bootstrap
```

The bootstrap command writes `AI_MODEL_ROOT/manifest.json` with the SHA-256 digest of
every model artifact. `AI_MODEL_MANIFEST` may point to a different manifest. In `real`
mode, readiness returns `503` and processing fails closed when the manifest is missing,
invalid, or lists a missing/altered file. Re-run the bootstrap command only after
obtaining trusted replacement assets; inspect the new inventory before restarting the
service. `hybrid` is intended for non-production use because it permits mock fallback.

Storage and encryption variables are shared with Django and documented in
[`.env.example`](../../.env.example). Never expose this port publicly or log media,
extracted identity attributes, embeddings, or the shared token.
