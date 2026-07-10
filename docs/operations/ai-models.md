# AI model provisioning

Bootstrap the pinned local model volume once:

```bash
docker compose --profile model-bootstrap run --rm ai-model-bootstrap
```

The command populates the `ai-models` volume and writes a `manifest.json` with artifact paths, sizes, and SHA-256 checksums. Normal services mount the volume with downloads disabled. Confirm readiness through authenticated `GET /v1/ready`.

- PaddleOCR supplies OCR and text-based document-type classification; this is not a dedicated visual document classifier.
- InsightFace `buffalo_l` supplies face embeddings and face matching.
- MediaPipe is installed with the service and supplies face-presence and passive-liveness signals.

Production should use an equivalent immutable volume or read-only artifact mount. Never enable mock or hybrid inference in production.
