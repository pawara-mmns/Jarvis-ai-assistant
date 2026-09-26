export interface VadConfig {
  speechStartThreshold: number;
  speechEndThreshold: number;
  minimumSpeechMs: number;
  speechEndDelayMs: number;
}

export const defaultVadConfig: VadConfig = {
  speechStartThreshold: 0.16,
  speechEndThreshold: 0.08,
  minimumSpeechMs: 120,
  speechEndDelayMs: 520,
};

export class EnergyVad {
  private speechDetected = false;
  private candidateStartedAt: number | null = null;
  private silenceStartedAt: number | null = null;

  constructor(private readonly config: VadConfig = defaultVadConfig) {}

  get isSpeechDetected(): boolean {
    return this.speechDetected;
  }

  update(level: number, timestampMs: number): boolean {
    if (!this.speechDetected) {
      this.silenceStartedAt = null;
      if (level >= this.config.speechStartThreshold) {
        this.candidateStartedAt ??= timestampMs;
        if (timestampMs - this.candidateStartedAt >= this.config.minimumSpeechMs) {
          this.speechDetected = true;
          this.candidateStartedAt = null;
        }
      } else {
        this.candidateStartedAt = null;
      }
      return this.speechDetected;
    }

    if (level <= this.config.speechEndThreshold) {
      this.silenceStartedAt ??= timestampMs;
      if (timestampMs - this.silenceStartedAt >= this.config.speechEndDelayMs) {
        this.speechDetected = false;
        this.silenceStartedAt = null;
      }
    } else {
      this.silenceStartedAt = null;
    }

    return this.speechDetected;
  }

  reset(): void {
    this.speechDetected = false;
    this.candidateStartedAt = null;
    this.silenceStartedAt = null;
  }
}
