# AI model provisioning and trust

Stop inference services before changing their model release. Fetch the approved PAD
candidate and bootstrap models using the writable bootstrap profile as described in
the [backend setup](../../backend/README.md). Bootstrap writes the complete inventory
and prints a **candidate** manifest SHA-256. That output is not independent approval.

Review the source/licensing, inventory and checksums through the trusted release
process. Pin the approved manifest's SHA-256 as `AI_MODEL_MANIFEST_SHA256` in deployment
configuration outside the model volume. Do not auto-populate it from the running
volume. `AI_MODEL_MANIFEST` selects the manifest file; it may remain beside the assets
because its expected digest is independently pinned. Replacing an asset and its
manifest together does not satisfy the configured digest.

Start the normal service with downloads disabled and an immutable model release.
Compose mounts `ai-models` read-only for inference and read-write only for the separate
bootstrap profile. Prevent concurrent bootstrap or other writers while inference is
running; a read-only mount does not prevent another container from changing the
underlying volume. Equivalent deployments must enforce the same access boundary.
Allow cold-start time for the streamed model verification before health probes.
Confirm authenticated `GET /v1/ready` before starting processing workers.
`make check-ai` runs the same credential-protected probe without exposing its token
and prints missing requirement codes. A failed `make up` attempts this diagnostic;
`make logs-ai` distinguishes a process crash from a running but unready service.

Real processing rejects absent/untrusted manifests, altered/missing/unlisted files,
a manifest selecting a different InsightFace model, omitted configured InsightFace
or PaddleOCR artifacts, symlink assets and enabled runtime downloads. Bootstrap
excludes the manifest by resolved identity, including an aliased model-root path.
Artifacts are hashed in bounded chunks. Startup warms the integrity check; subsequent
requests/readiness inspect filesystem metadata, reusing digests while the complete
inventory and configured release remain unchanged. Additions, removals, inode/size/
mtime/ctime changes or a changed trust anchor invalidate it. This reduces warm checks
to metadata work; it is not a guarantee against a privileged writer racing inference.
Use immutable/read-only releases and restart all workers for a new approved model.
No automatic in-process model replacement or approval is performed.

- PaddleOCR supplies OCR; document classification uses the AI-service evidence classifier.
- InsightFace `buffalo_l` supplies embeddings and face matching.
- MediaPipe is installed with the service and supplies face-presence/passive signals.
- Country coverage uses `DOCUMENT_CLASSIFICATION_ENABLED_COUNTRY_CODES`.

Synthetic integrity tests do not establish model accuracy, real startup performance,
malware safety or readiness for production. Physical/device/adversarial evaluation
and release approval remain required. Never enable mock or hybrid in production.

The AI image installs only `opencv-contrib-python==5.0.0.93`. PaddleX checks this
distribution name both for OCR dependencies and for conditional `cv2` imports;
the headless contrib distribution alone leaves its image reader unusable. The
frozen dependency exclusions and runtime guard reject overlapping OpenCV wheels.
The image build also checks the real PaddleX OCR-core dependencies and constructs
its RGB image reader, without downloading models. Keep the existing OS libraries;
no display server or GUI calls are used by IdentityCore's inference pipeline.

For the commercially permitted OpenCV candidate, choose
`FACE_EMBEDDING_ENGINE=opencv_sface`, fetch with the pinned
`scripts/fetch_face_models.py` before bootstrapping, and review the generated
`face_engine`/`face_models` manifest fields. Both ONNX files and their license notices
must be present in the approved inventory. Inference does not fall back to legacy
weights. Provision a separate clean model root containing only the selected face
engine, PAD and Paddle assets; stop inference before changing the mounted release.
See [model-licenses.md](model-licenses.md) for immutable provenance and licensing.
