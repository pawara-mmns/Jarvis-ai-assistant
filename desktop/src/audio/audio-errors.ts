export function getMicrophoneErrorMessage(error: unknown): string {
  if (!(error instanceof DOMException)) return "Unable to access the microphone.";

  switch (error.name) {
    case "NotAllowedError":
    case "SecurityError":
      return "Microphone permission was denied.";
    case "NotFoundError":
    case "OverconstrainedError":
      return "No compatible microphone was detected.";
    case "NotReadableError":
    case "TrackStartError":
      return "The microphone is unavailable or already in use.";
    case "AbortError":
      return "Microphone startup was interrupted.";
    default:
      return "Unable to access the microphone.";
  }
}
