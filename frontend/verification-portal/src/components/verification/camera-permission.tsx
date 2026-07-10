"use client";

import { Camera, ShieldAlert } from "lucide-react";
import { Button } from "@identitycore/ui";

interface CameraPermissionProps {
  onAllow: () => void;
  onDenied: () => void;
}

export function CameraPermission({ onAllow, onDenied }: CameraPermissionProps) {
  return (
    <div className="rounded-4xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
        <Camera className="h-6 w-6" aria-hidden="true" />
      </div>

      <h2 className="mt-5 text-xl font-semibold">Camera access required</h2>

      <p className="mx-auto mt-2 max-w-md text-sm leading-7 text-slate-600">
        IdentityCore needs camera access to capture your identity document,
        selfie, and liveness evidence.
      </p>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <Button type="button" onClick={onAllow} className="rounded-xl">
          Allow camera
        </Button>

        <Button
          type="button"
          variant="outline"
          onClick={onDenied}
          className="rounded-xl"
        >
          <ShieldAlert className="h-4 w-4" aria-hidden="true" />I cannot use
          camera
        </Button>
      </div>
    </div>
  );
}
