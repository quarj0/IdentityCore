"use client";

import { useEffect, useRef, useState } from "react";
import { Camera, Loader2, RefreshCw, Upload } from "lucide-react";
import { Button, Input } from "@identitycore/ui";

export function CameraCapture({
  facingMode,
  label,
  onCapture,
}: {
  facingMode: "user" | "environment";
  label: string;
  onCapture: (file: File) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [starting, setStarting] = useState(false);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function stopCamera() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setActive(false);
  }

  useEffect(() => stopCamera, []);

  async function startCamera() {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setError("Camera access requires HTTPS or localhost and a supported browser.");
      return;
    }
    stopCamera();
    setStarting(true);
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: { ideal: facingMode }, width: { ideal: 1280 } },
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
          ? "Camera permission was denied. Enable it in browser settings or upload a file."
          : "No usable camera was found. You can upload a file instead.",
      );
    } finally {
      setStarting(false);
    }
  }

  function capture() {
    const video = videoRef.current;
    if (!video?.videoWidth || !video.videoHeight) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        onCapture(new File([blob], `${facingMode}-capture.jpg`, { type: "image/jpeg" }));
        stopCamera();
      },
      "image/jpeg",
      0.9,
    );
  }

  return (
    <div className="space-y-4 rounded-3xl border border-slate-200 bg-slate-950 p-4 text-white">
      <video
        ref={videoRef}
        muted
        playsInline
        aria-label={label}
        className="aspect-[4/3] w-full rounded-2xl bg-slate-900 object-cover"
      />
      {error ? <p role="alert" className="text-sm text-amber-300">{error}</p> : null}
      <div className="grid gap-3 sm:grid-cols-2">
        {!active ? (
          <Button type="button" onClick={startCamera} disabled={starting}>
            {starting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
            Allow camera
          </Button>
        ) : (
          <Button type="button" onClick={capture}><Camera className="h-4 w-4" />Capture</Button>
        )}
        <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-white/20 px-4 py-2 text-sm font-medium">
          <Upload className="h-4 w-4" /> Upload instead
          <Input className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) { stopCamera(); onCapture(file); }
          }} />
        </label>
      </div>
      {active ? <Button type="button" variant="ghost" onClick={startCamera} className="text-white"><RefreshCw className="h-4 w-4" />Restart camera</Button> : null}
    </div>
  );
}
