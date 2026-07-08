import { FileUp, ImagePlus } from "lucide-react";
import { Button } from "@identitycore/ui";

interface UploadFallbackProps {
  title: string;
  description: string;
  onUploaded: () => void;
  onBackToCamera: () => void;
}

export function UploadFallback({
  title,
  description,
  onUploaded,
  onBackToCamera,
}: UploadFallbackProps) {
  return (
    <div className="rounded-[2rem] border border-dashed border-slate-300 bg-white p-6 text-center shadow-sm">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
        <FileUp className="h-6 w-6" aria-hidden="true" />
      </div>

      <h2 className="mt-5 text-xl font-semibold">{title}</h2>

      <p className="mx-auto mt-2 max-w-md text-sm leading-7 text-slate-600">
        {description}
      </p>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-8">
        <ImagePlus className="mx-auto h-8 w-8 text-slate-500" />
        <p className="mt-3 text-sm font-medium">Drop file here or browse</p>
        <p className="mt-1 text-xs text-slate-500">
          UI-only upload fallback for now.
        </p>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <Button type="button" onClick={onUploaded} className="rounded-xl">
          Use mock upload
        </Button>

        <Button
          type="button"
          variant="outline"
          onClick={onBackToCamera}
          className="rounded-xl"
        >
          Back to camera
        </Button>
      </div>
    </div>
  );
}
