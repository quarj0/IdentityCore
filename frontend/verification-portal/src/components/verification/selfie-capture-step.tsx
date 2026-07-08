import { CapturePanel } from "./capture-panel";
import { MockCamera } from "./mock-camera";
import { StepActions } from "./step-actions";

interface SelfieCaptureStepProps {
  onCapture: () => void;
  onUpload: () => void;
  onBack: () => void;
}

export function SelfieCaptureStep({
  onCapture,
  onUpload,
  onBack,
}: SelfieCaptureStepProps) {
  return (
    <CapturePanel
      title="Capture your selfie"
      description="Look straight at the camera and make sure your face is clearly visible."
    >
      <MockCamera
        label="Selfie capture"
        helperText="Use good lighting and remove hats or sunglasses."
        onCapture={onCapture}
        onUpload={onUpload}
      />

      <StepActions onBack={onBack} />
    </CapturePanel>
  );
}
