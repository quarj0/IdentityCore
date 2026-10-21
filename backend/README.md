# IdentityCore backend

The backend workspace contains the Django control plane and the internal FastAPI AI
service. Run these commands from the repository root. For the real-mode stack,
copy the development configuration, then configure its storage endpoints/credentials,
internal service token and other required settings before starting services:

```bash
cp .env.example .env
```

Real mode requires provisioned model assets; runtime downloads are disabled. Fetch
the pinned PAD candidate and bootstrap the named model volume before starting the
workers (see the [AI model guide](ai-service/README.md) for approval and checksum
requirements). These downloads need network access and disk space; they do not
establish biometric accuracy or production approval:

```bash
docker compose --profile model-bootstrap run --rm --build --entrypoint python \
  ai-model-bootstrap /app/scripts/fetch_pad_model.py \
  --model-root /opt/identitycore/models
docker compose --profile model-bootstrap run --rm --entrypoint python \
  ai-model-bootstrap /app/scripts/fetch_face_models.py \
  --model-root /opt/identitycore/models
docker compose --profile model-bootstrap run --rm ai-model-bootstrap
# Review the candidate manifest and configure AI_MODEL_MANIFEST_SHA256 in .env.
# Follow docs/operations/ai-models.md; do not trust a digest from a mutable volume automatically.
docker compose up --build -d
curl http://localhost:8000/api/v1/health
curl -H "X-Internal-Token: $(sed -n 's/^AI_SERVICE_SHARED_TOKEN=//p' .env)" http://localhost:8001/v1/ready
```

PostgreSQL is exposed on `5433`, Redis on `6379`, Django on `8000`, and the AI
service on `8001`. The Celery workers and scheduler have no host ports. See
[`django/README.md`](django/README.md) and [`ai-service/README.md`](ai-service/README.md)
for service-specific commands and configuration. The root [`.env.example`](../.env.example)
is the authoritative variable list; its values are for local development only.

Run all backend tests with `make test` and static checks with `make lint`.


## AI startup diagnostics

If `make up` fails, it attempts the AI readiness diagnostic while preserving the
original startup failure status. `make check-ai` runs the same authenticated probe
as the Compose healthcheck and
prints the missing requirement codes without credentials or raw responses.
`make logs-ai` shows the service startup log. A running process with `/v1/ready`
returning 503 is not ready for real inference: provision the reviewed model bundle,
pin `AI_MODEL_MANIFEST_SHA256`, and configure the object-storage values above.
Changing to mock/hybrid or weakening the probe does not fix real inference readiness.
If the process exits or restarts, inspect `docker compose logs --tail=40 ai-service`
for the import/runtime/configuration error before retrying `make up`.

### AI image download timeout

If the build reports `ReadTimeoutError` from `files.pythonhosted.org` while
installing a wheel, the image build failed before the new AI process started.
Retry `docker compose build ai-service`, then `make up`. The AI Dockerfile uses
BuildKit's pip cache so completed downloads survive a failed build, a 120-second
socket timeout and five connection retries. For a persistently slow link, use:

```bash
docker compose build --build-arg PIP_DEFAULT_TIMEOUT=300 --build-arg PIP_RETRIES=10 ai-service
docker compose up -d --no-build
```

The cache does not resume a partially downloaded wheel; that file may need to be
downloaded again. Keep TLS verification enabled. If the later readiness probe
reports `models.manifest_missing`, `models.pad`, `models.insightface` or
`models.paddleocr.*`, complete the model provisioning and manifest approval steps
above. A failed rebuild can leave an older AI container running, so its readiness
output describes that existing container rather than a successfully rebuilt image.

### AI dependency security baseline

The backend manifest and lockfile require Pillow 13.0.0 or newer and certifi
2026.10.19 or newer. These updates address the Pillow image-decoder advisories
and [compromised emSign CA roots in certifi](https://github.com/advisories/GHSA-6q48-6c7w-9gw2).
Rebuild after pulling dependency updates; an existing container retains its old
installed packages until replaced. The documented
[frontend dependency backports](../docs/operations/frontend-dependency-security.md)
remain separate, version-visible mitigations.

### Face model selection

New `.env.example` configurations select `FACE_EMBEDDING_ENGINE=opencv_sface`.
The pinned fetch script provisions OpenCV Zoo YuNet (MIT) and SFace (Apache 2.0),
including their license notices. Bootstrap writes the selected engine and weight
paths into the candidate manifest. Inference still requires independent manifest
approval. Existing installations without the setting retain the legacy InsightFace
engine for compatibility; its downloaded `buffalo_l` weights are restricted to
non-commercial research unless separately licensed. Do not approve them for a
commercial pilot by treating the Python package's MIT license as a weight license.

Switching engines requires a new reviewed immutable model release and restart.
Existing matching thresholds are retained; SFace scores require separate calibration
and held-out evaluation. The license permits a use; it does not establish biometric
accuracy, fairness, liveness performance or customer-launch approval. See the
[model license record](../docs/operations/model-licenses.md).
