import { Camera, Upload } from "lucide-react";
import { Button } from "@identitycore/ui";

interface MockCameraProps {
  label: string;
  helperText?: string;
  onCapture: () => void;
  onUpload?: () => void;
}

export function MockCamera({
  label,
  helperText = "Position clearly inside the frame.",
  onCapture,
  onUpload,
}: MockCameraProps) {
  return (
    <div className="rounded-[2rem] bg-slate-950 p-4 text-center text-white sm:p-5">
      <div
        className="flex min-h-[320px] items-center justify-center rounded-3xl border border-slate-200 bg-white/[0.04]"
        role="img"
        aria-label={label}
      >
        <div>
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10 text-blue-300">
            <Camera className="h-7 w-7" aria-hidden="true" />
          </div>
          <p className="mt-5 text-sm font-medium">{label}</p>
          <p className="mt-1 max-w-xs text-xs leading-6 text-slate-400">
            {helperText}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {onUpload ? (
          <Button
            type="button"
            variant="outline"
            onClick={onUpload}
            className="rounded-xl border-slate-200 bg-white/5 text-white hover:bg-white/10"
          >
            <Upload className="h-4 w-4" aria-hidden="true" />
            Upload instead
          </Button>
        ) : null}

        <Button type="button" onClick={onCapture} className="rounded-xl">
          Capture mock image
        </Button>
      </div>
    </div>
  );
}
