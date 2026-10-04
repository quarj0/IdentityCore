// Capture methods are client reports, never proof of a physical camera.
type CaptureMethod = "camera" | "live_recording" | "file";
const methods = new WeakMap<File, CaptureMethod>();

export function recordCapture(file: File, method: CaptureMethod): File {
  methods.set(file, method);
  return file;
}

export function reportedCaptureMethod(file: File): CaptureMethod {
  return methods.get(file) ?? "file";
}
