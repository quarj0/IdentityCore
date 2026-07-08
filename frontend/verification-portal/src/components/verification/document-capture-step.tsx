import { CapturePanel } from "./capture-panel";
import { MockCamera } from "./mock-camera";
import { StepActions } from "./step-actions";

interface DocumentCaptureStepProps {
  side: "front" | "back";
  documentType: string;
  onCapture: () => void;
  onUpload: () => void;
  onBack: () => void;
}

export function DocumentCaptureStep({
  side,
  documentType,
  onCapture,
  onUpload,
  onBack,
}: DocumentCaptureStepProps) {
  return (
    <CapturePanel
      title={`Capture ${side} of ${documentType}`}
      description="Make sure the document is clear, readable, and fully inside the frame."
    >
      <MockCamera
        label={`${documentType} ${side} capture`}
        helperText="Avoid glare and keep all corners visible."
        onCapture={onCapture}
        onUpload={onUpload}
      />

      <StepActions onBack={onBack} />
    </CapturePanel>
  );
}
