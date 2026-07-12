# AI model provisioning

Bootstrap the pinned local model volume once:

```bash
docker compose --profile model-bootstrap run --rm ai-model-bootstrap
```

The command populates the `ai-models` volume and writes a `manifest.json` with artifact paths, sizes, and SHA-256 checksums. Normal services mount the volume with downloads disabled. Confirm readiness through authenticated `GET /v1/ready`.

- PaddleOCR supplies OCR only; document classification is handled by the AI-service evidence classifier on top of OCR output.
- InsightFace `buffalo_l` supplies face embeddings and face matching.
- MediaPipe is installed with the service and supplies face-presence and passive-liveness signals.
- The document-classification registry is settings-driven via `DOCUMENT_CLASSIFICATION_ENABLED_COUNTRY_CODES`.
- The classifier uses OCR similarity plus OCR confidence and MRZ evidence, rather than filename heuristics or manually assigned document scores.

Production should use an equivalent immutable volume or read-only artifact mount. Never enable mock or hybrid inference in production.
