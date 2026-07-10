import { useState } from "react";
import { Smile, Video } from "lucide-react";
import { Button } from "@identitycore/ui";
import { CapturePanel } from "./capture-panel";
import { StepActions } from "./step-actions";

interface LivenessStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function LivenessStep({ onNext, onBack }: LivenessStepProps) {
  const [challenge, setChallenge] = useState(0);
  const challenges = ["Blink twice", "Turn your head slightly", "Look forward"];

  return (
    <CapturePanel
      title="Complete liveness check"
      description="Follow the short challenge to confirm a real person is present."
    >
      <div className="rounded-4xl bg-slate-950 p-8 text-center text-white">
        <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-full bg-white/10">
          <Smile className="h-14 w-14 text-blue-300" />
        </div>

        <p className="mt-6 text-sm font-medium">
          Challenge: {challenges[challenge]}
        </p>

        <p className="mt-2 text-sm text-slate-500">Mock liveness challenge</p>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <Button
            type="button"
            onClick={() =>
              challenge < challenges.length - 1
                ? setChallenge((value) => value + 1)
                : onNext()
            }
            className="rounded-xl"
          >
            <Video className="h-4 w-4" />
            {challenge < challenges.length - 1
              ? "Next challenge"
              : "Pass liveness"}
          </Button>

          <Button
            type="button"
            variant="outline"
            onClick={() => setChallenge(0)}
            className="rounded-xl border-slate-200 bg-white/5 text-white hover:bg-white/10"
          >
            Restart
          </Button>
        </div>
      </div>

      <StepActions onBack={onBack} />
    </CapturePanel>
  );
}
