# Synthetic video fixtures

These one-second 64x64 solid-blue clips contain no people or applicant data.
They were generated for IdentityCore with FFmpeg's `color` source, five frames per
second, no audio, and H.264 (`libx264`, yuv420p) or VP8 (`libvpx`, yuv420p).
They exercise browser-capture video formats through OpenCV's bundled decoder;
the AI runtime does not need the external FFmpeg command-line package.

Example generation input: `-f lavfi -i color=c=blue:s=64x64:r=5 -t 1 -an`.
These are functional codec checks, not adversarial media or liveness evaluations.
