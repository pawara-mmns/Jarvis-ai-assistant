export function mergeTranscript(current: string, incoming: string): string {
  if (!incoming) return current;
  if (!current) return incoming.trimStart();
  if (incoming.startsWith(current)) return incoming;
  if (current.endsWith(incoming)) return current;

  const maxOverlap = Math.min(current.length, incoming.length);
  for (let overlap = maxOverlap; overlap > 0; overlap -= 1) {
    if (current.endsWith(incoming.slice(0, overlap))) {
      return current + incoming.slice(overlap);
    }
  }

  const needsSpace = !/\s$/.test(current) && !/^[\s.,!?;:)}\]]/.test(incoming);
  return `${current}${needsSpace ? " " : ""}${incoming}`;
}

