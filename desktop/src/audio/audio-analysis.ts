export interface AudioNormalizationOptions {
  noiseFloor: number;
  referenceLevel: number;
  responseCurve: number;
}

export interface AudioSmoothingOptions {
  attack: number;
  release: number;
}

export const defaultNormalizationOptions: AudioNormalizationOptions = {
  noiseFloor: 0.008,
  referenceLevel: 0.16,
  responseCurve: 0.72,
};

export const defaultSmoothingOptions: AudioSmoothingOptions = {
  attack: 0.4,
  release: 0.12,
};

export function clampUnit(value: number): number {
  return Math.min(1, Math.max(0, value));
}

export function calculateRms(samples: ArrayLike<number>): number {
  if (samples.length === 0) return 0;

  let squareSum = 0;
  for (let index = 0; index < samples.length; index += 1) {
    const sample = samples[index] ?? 0;
    squareSum += sample * sample;
  }

  return Math.sqrt(squareSum / samples.length);
}

export function normalizeAudioLevel(
  rms: number,
  options: AudioNormalizationOptions = defaultNormalizationOptions,
): number {
  if (rms <= options.noiseFloor) return 0;
  const usableRange = Math.max(0.0001, options.referenceLevel - options.noiseFloor);
  const normalized = clampUnit((rms - options.noiseFloor) / usableRange);
  return clampUnit(Math.pow(normalized, options.responseCurve));
}

export function smoothAudioLevel(
  previous: number,
  next: number,
  options: AudioSmoothingOptions = defaultSmoothingOptions,
): number {
  const coefficient = next > previous ? options.attack : options.release;
  return clampUnit(previous + (next - previous) * clampUnit(coefficient));
}

export function summarizeWaveform(
  samples: ArrayLike<number>,
  barCount = 24,
  normalization: AudioNormalizationOptions = defaultNormalizationOptions,
): number[] {
  if (barCount <= 0) return [];

  const levels = new Array<number>(barCount).fill(0);
  if (samples.length === 0) return levels;

  const bucketSize = Math.max(1, Math.floor(samples.length / barCount));
  for (let barIndex = 0; barIndex < barCount; barIndex += 1) {
    const start = barIndex * bucketSize;
    const end = barIndex === barCount - 1 ? samples.length : Math.min(samples.length, start + bucketSize);
    let squareSum = 0;
    let count = 0;

    for (let sampleIndex = start; sampleIndex < end; sampleIndex += 1) {
      const sample = samples[sampleIndex] ?? 0;
      squareSum += sample * sample;
      count += 1;
    }

    const rms = count ? Math.sqrt(squareSum / count) : 0;
    levels[barIndex] = normalizeAudioLevel(rms, normalization);
  }

  return levels;
}

export function smoothWaveform(
  previous: readonly number[],
  next: readonly number[],
  coefficient = 0.34,
): number[] {
  const amount = clampUnit(coefficient);
  return next.map((level, index) => {
    const previousLevel = previous[index] ?? 0;
    return clampUnit(previousLevel + (level - previousLevel) * amount);
  });
}
