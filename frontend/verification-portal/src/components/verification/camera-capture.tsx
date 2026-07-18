"use client";

import { useEffect, useRef, useState } from "react";
import { Camera, ImagePlus, Loader2, RefreshCw, Upload } from "lucide-react";

import { Button, Input } from "@identitycore/ui";

interface CameraCaptureProps {
  facingMode: "user" | "environment";
  label: string;
  onCapture: (file: File) => void;
}

export function CameraCapture({
  facingMode,
  label,
  onCapture,
}: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [starting, setStarting] = useState(false);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function stopCamera() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setActive(false);
  }

  useEffect(() => stopCamera, []);

  async function startCamera() {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setError("Camera access requires HTTPS or localhost. You can upload an image instead.");
      return;
    }

    stopCamera();
    setStarting(true);
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: { ideal: facingMode },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setActive(true);
    } catch (caught) {
      const name = caught instanceof DOMException ? caught.name : "";
      setError(
        name === "NotAllowedError"
          ? "Camera permission is blocked. Enable it in your browser settings or upload an image."
          : "We could not start a usable camera. Upload a clear image to continue.",
      );
    } finally {
      setStarting(false);
    }
  }

  function capture() {
    const video = videoRef.current;
    if (!video?.videoWidth || !video.videoHeight) {
      setError("The camera is still preparing. Wait a moment and try again.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) {
      setError("Your browser could not capture this image. Upload one instead.");
      return;
    }
    context.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError("The image could not be created. Please try again.");
          return;
        }
        onCapture(
          new File([blob], `${facingMode}-capture-${Date.now()}.jpg`, {
            type: "image/jpeg",
          }),
        );
        stopCamera();
      },
      "image/jpeg",
      0.92,
    );
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-950 shadow-inner">
      <div className="relative aspect-4/3 overflow-hidden bg-slate-900">
        <video
          ref={videoRef}
          muted
          playsInline
          aria-label={label}
          className={`h-full w-full object-cover ${facingMode === "user" ? "-scale-x-100" : ""}`}
        />
        {!active ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center px-6 text-center text-slate-300">
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-white/10">
              <Camera className="h-6 w-6" aria-hidden="true" />
            </span>
            <p className="mt-4 text-sm font-medium text-white">Camera preview</p>
            <p className="mt-1 max-w-xs text-xs leading-5 text-slate-400">
              Allow camera access when prompted. Nothing is submitted until you review the image.
            </p>
          </div>
        ) : facingMode === "environment" ? (
          <div className="pointer-events-none absolute inset-[8%] rounded-2xl border-2 border-white/80 shadow-[0_0_0_999px_rgba(2,6,23,0.36)]">
            <span className="absolute -top-8 left-0 text-xs font-medium text-white">
              Align the full document inside the frame
            </span>
          </div>
        ) : (
          <div className="pointer-events-none absolute left-1/2 top-1/2 h-[72%] w-[58%] -translate-x-1/2 -translate-y-1/2 rounded-[48%] border-2 border-white/80 shadow-[0_0_0_999px_rgba(2,6,23,0.3)]" />
        )}
      </div>

      {error ? (
        <p role="alert" className="border-t border-white/10 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
          {error}
        </p>
      ) : null}

      <div className="flex flex-col gap-3 p-4 sm:flex-row">
        {!active ? (
          <Button type="button" onClick={startCamera} disabled={starting} className="flex-1">
            {starting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
            {starting ? "Starting camera…" : "Use camera"}
          </Button>
        ) : (
          <Button type="button" onClick={capture} className="flex-1">
            <Camera className="h-4 w-4" />
            Capture image
          </Button>
        )}

        <label className="inline-flex min-h-10 flex-1 cursor-pointer items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/10">
          <Upload className="h-4 w-4" aria-hidden="true" />
          Upload image
          <Input
            className="sr-only"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (file) {
                stopCamera();
                onCapture(file);
              }
            }}
          />
        </label>
      </div>

      {active ? (
        <div className="flex items-center justify-between border-t border-white/10 px-4 py-3">
          <p className="flex items-center gap-2 text-xs text-slate-400">
            <ImagePlus className="h-3.5 w-3.5" aria-hidden="true" />
            Check focus and lighting before capture
          </p>
          <Button type="button" size="sm" variant="ghost" onClick={startCamera} className="text-white hover:bg-white/10 hover:text-white">
            <RefreshCw className="h-3.5 w-3.5" />
            Restart
          </Button>
        </div>
      ) : null}
    </div>
  );
}
