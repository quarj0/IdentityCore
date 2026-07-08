import { CameraOff, Upload } from "lucide-react";
import { Button } from "@identitycore/ui";

interface CameraUnavailableProps {
  onUpload: () => void;
  onRetry: () => void;
}

export function CameraUnavailable({
  onUpload,
  onRetry,
}: CameraUnavailableProps) {
  return (
    <div className="rounded-[2rem] border border-amber-200 bg-amber-50 p-6 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-amber-700 ring-1 ring-amber-100">
        <CameraOff className="h-6 w-6" aria-hidden="true" />
      </div>

      <h2 className="mt-5 text-xl font-semibold text-amber-950">
        Camera unavailable
      </h2>

      <p className="mx-auto mt-2 max-w-md text-sm leading-7 text-amber-800">
        We could not access your camera. You can retry or upload a file instead.
      </p>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <Button type="button" onClick={onRetry} className="rounded-xl">
          Retry camera
        </Button>

        <Button
          type="button"
          variant="outline"
          onClick={onUpload}
          className="rounded-xl bg-white"
        >
          <Upload className="h-4 w-4" aria-hidden="true" />
          Upload instead
        </Button>
      </div>
    </div>
  );
}
