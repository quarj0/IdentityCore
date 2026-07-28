export interface RecordingFormat {
  recorderMimeType: string;
  fileMimeType: "video/mp4" | "video/webm";
  extension: "mp4" | "webm";
}

const RECORDING_FORMATS: RecordingFormat[] = [
  {
    recorderMimeType: "video/mp4",
    fileMimeType: "video/mp4",
    extension: "mp4",
  },
  {
    recorderMimeType: "video/mp4;codecs=avc1.42E01E",
    fileMimeType: "video/mp4",
    extension: "mp4",
  },
  {
    recorderMimeType: "video/webm;codecs=vp8",
    fileMimeType: "video/webm",
    extension: "webm",
  },
  {
    recorderMimeType: "video/webm;codecs=vp9",
    fileMimeType: "video/webm",
    extension: "webm",
  },
  {
    recorderMimeType: "video/webm",
    fileMimeType: "video/webm",
    extension: "webm",
  },
];

export function selectRecordingFormat(
  isTypeSupported: (mimeType: string) => boolean,
) {
  return RECORDING_FORMATS.find((format) => {
    try {
      return isTypeSupported(format.recorderMimeType);
    } catch {
      return false;
    }
  });
}
