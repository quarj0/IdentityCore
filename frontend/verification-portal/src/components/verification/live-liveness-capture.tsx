"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Camera, CircleStop, Loader2, Play, RotateCcw } from "lucide-react";

import { Button } from "@identitycore/ui";
import { selectRecordingFormat } from "@/lib/media-recording";

const ACTION_LABELS: Record<string, string> = {
  turn_left: "Turn your head left",
  turn_right: "Turn your head right",
  look_up: "Look up",
  look_down: "Look down",
};
const MAX_RECORDING_BYTES = 25 * 1024 * 1024;
const MAX_RECORDING_MS = 15_000;

export function LiveLivenessCapture({
  actions,
  onCapture,
}: {
  actions: string[];
  onCapture: (file: File) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const discardRecordingRef = useRef(false);
  const stoppingCameraRef = useRef(false);
  const [starting, setStarting] = useState(false);
  const [active, setActive] = useState(false);
  const [recording, setRecording] = useState(false);
  const [actionIndex, setActionIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const stopCamera = useCallback(() => {
    stoppingCameraRef.current = true;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setActive(false);
    stoppingCameraRef.current = false;
  }, []);

  const cancelRecording = useCallback(
    (message: string) => {
      discardRecordingRef.current = true;
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      } else {
        stopCamera();
      }
      setRecording(false);
      setError(message);
    },
    [stopCamera],
  );

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && recorderRef.current?.state === "recording") {
        cancelRecording(
          "The live check was interrupted when this page became inactive. Start it again.",
        );
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      discardRecordingRef.current = true;
      if (recorderRef.current?.state === "recording")
        recorderRef.current.stop();
      stopCamera();
    };
  }, [cancelRecording, stopCamera]);

  async function startCamera() {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setError(
        "Live liveness requires a secure HTTPS connection and camera access.",
      );
      return;
    }
    if (typeof MediaRecorder === "undefined") {
      setError(
        "This browser cannot record a live liveness video. Use a current browser on your phone.",
      );
      return;
    }

    stopCamera();
    setStarting(true);
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: { ideal: "user" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      });
      streamRef.current = stream;
      stream.getVideoTracks()[0]?.addEventListener(
        "ended",
        () => {
          if (stoppingCameraRef.current) return;
          if (recorderRef.current?.state === "recording") {
            cancelRecording(
              "The camera disconnected during the live check. Start it again.",
            );
          } else {
            stopCamera();
            setError(
              "The camera is no longer available. Enable it and try again.",
            );
          }
        },
        { once: true },
      );
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        // Camera readiness is represented by getUserMedia succeeding. Awaiting play()
        // can hang when a browser or test double has no decodable video frames.
        void videoRef.current.play().catch(() => undefined);
      }
      setActive(true);
    } catch {
      setError(
        "Camera access is required for this live check. Allow camera access and try again.",
      );
    } finally {
      setStarting(false);
    }
  }

  function finishRecording() {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  }

  function startRecording() {
    if (!streamRef.current) return;
    const format = selectRecordingFormat((mimeType) =>
      MediaRecorder.isTypeSupported(mimeType),
    );
    if (!format) {
      setError(
        "This browser cannot create a supported MP4 or WebM liveness video. Update your browser or use another current device.",
      );
      return;
    }

    chunksRef.current = [];
    discardRecordingRef.current = false;
    setActionIndex(0);
    setError(null);
    const recorder = new MediaRecorder(streamRef.current, {
      mimeType: format.recorderMimeType,
      videoBitsPerSecond: 1_500_000,
    });
    recorderRef.current = recorder;
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: format.fileMimeType });
      if (discardRecordingRef.current) {
        chunksRef.current = [];
      } else if (!blob.size) {
        setError("No video was recorded. Please try again.");
      } else if (blob.size > MAX_RECORDING_BYTES) {
        setError(
          "The live video is too large to upload. Move closer to a stable connection and try again.",
        );
      } else {
        onCapture(
          new File([blob], `liveness-${Date.now()}.${format.extension}`, {
            type: format.fileMimeType,
          }),
        );
      }
      setRecording(false);
      stopCamera();
    };
    recorder.start();
    setRecording(true);
  }

  useEffect(() => {
    if (!recording) return;
    if (actionIndex >= actions.length) {
      const timer = window.setTimeout(finishRecording, 1200);
      return () => window.clearTimeout(timer);
    }
    const timer = window.setTimeout(
      () => setActionIndex((index) => index + 1),
      2500,
    );
    return () => window.clearTimeout(timer);
  }, [actionIndex, actions.length, recording]);

  useEffect(() => {
    if (!recording) return;
    const timer = window.setTimeout(() => finishRecording(), MAX_RECORDING_MS);
    return () => window.clearTimeout(timer);
  }, [recording]);

  const currentAction = actions[actionIndex];
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-950 shadow-inner">
      <div className="relative aspect-4/3 overflow-hidden bg-slate-900">
        <video
          ref={videoRef}
          muted
          playsInline
          className="h-full w-full -scale-x-100 object-cover"
        />
        {!active ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center px-6 text-center text-slate-300">
            <Camera className="h-7 w-7" />
            <p className="mt-3 text-sm font-medium text-white">
              Live camera check
            </p>
            <p className="mt-1 max-w-xs text-xs leading-5 text-slate-400">
              A short video is recorded only after you start the challenge.
            </p>
          </div>
        ) : null}
        {recording ? (
          <div className="absolute inset-x-4 top-4 rounded-2xl bg-blue-700 px-4 py-3 text-center text-sm font-semibold text-white shadow-lg">
            <span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-red-300" />
            {currentAction
              ? (ACTION_LABELS[currentAction] ?? currentAction)
              : "Hold still while we finish recording"}
          </div>
        ) : null}
        {active ? (
          <div className="pointer-events-none absolute left-1/2 top-1/2 h-[72%] w-[58%] -translate-x-1/2 -translate-y-1/2 rounded-[48%] border-2 border-white/80 shadow-[0_0_0_999px_rgba(2,6,23,0.3)]" />
        ) : null}
      </div>
      {error ? (
        <p
          role="alert"
          className="border-t border-amber-300/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100"
        >
          {error}
        </p>
      ) : null}
      <div className="flex gap-3 p-4">
        {!active ? (
          <Button
            type="button"
            onClick={startCamera}
            disabled={starting}
            className="flex-1"
          >
            {starting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Camera className="h-4 w-4" />
            )}
            {starting ? "Starting camera…" : "Enable camera"}
          </Button>
        ) : !recording ? (
          <Button type="button" onClick={startRecording} className="flex-1">
            <Play className="h-4 w-4" />
            Start live challenge
          </Button>
        ) : (
          <Button
            type="button"
            variant="outline"
            onClick={finishRecording}
            className="flex-1"
          >
            <CircleStop className="h-4 w-4" />
            Finish recording
          </Button>
        )}
        {active && !recording ? (
          <Button
            type="button"
            variant="ghost"
            onClick={startCamera}
            className="text-white hover:bg-white/10 hover:text-white"
          >
            <RotateCcw className="h-4 w-4" />
            Restart
          </Button>
        ) : null}
      </div>
    </div>
  );
}
