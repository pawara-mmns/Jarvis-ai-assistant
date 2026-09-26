import { z } from "zod";

export const LIVE_MESSAGE_TYPES = {
  sessionStart: "session.start",
  audioChunk: "audio.chunk",
  audioEnd: "audio.end",
  sessionStop: "session.stop",
  sessionConnected: "session.connected",
  sessionReady: "session.ready",
  sessionState: "session.state",
  transcriptInput: "transcript.input",
  transcriptOutput: "transcript.output",
  audioOutput: "audio.output",
  toolStarted: "tool.started",
  toolCompleted: "tool.completed",
  toolFailed: "tool.failed",
  turnComplete: "turn.complete",
  sessionInterrupted: "session.interrupted",
  sessionError: "session.error",
  sessionClosed: "session.closed",
} as const;

const audioMimeTypeSchema = z.string().regex(/^audio\/pcm;rate=\d+$/);

export const liveClientMessageSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.sessionStart),
    bridgeToken: z.string().min(32),
  }),
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.audioChunk),
    data: z.string().min(1),
    mimeType: z.literal("audio/pcm;rate=16000"),
  }),
  z.object({ type: z.literal(LIVE_MESSAGE_TYPES.audioEnd) }),
  z.object({ type: z.literal(LIVE_MESSAGE_TYPES.sessionStop) }),
]);

const transcriptSchema = z.object({
  text: z.string(),
  final: z.boolean().default(false),
});

export const liveServerMessageSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal(LIVE_MESSAGE_TYPES.sessionConnected) }),
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.sessionReady),
    model: z.string(),
    inputSampleRate: z.number().int().positive(),
    outputSampleRate: z.number().int().positive(),
  }),
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.sessionState),
    state: z.enum(["connecting", "ready", "reconnecting"]),
    attempt: z.number().int().nonnegative().optional(),
  }),
  transcriptSchema.extend({ type: z.literal(LIVE_MESSAGE_TYPES.transcriptInput) }),
  transcriptSchema.extend({ type: z.literal(LIVE_MESSAGE_TYPES.transcriptOutput) }),
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.audioOutput),
    data: z.string().min(1),
    mimeType: audioMimeTypeSchema,
  }),
  z.object({ type: z.literal(LIVE_MESSAGE_TYPES.turnComplete) }),
  z.object({ type: z.literal(LIVE_MESSAGE_TYPES.sessionInterrupted) }),
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.toolStarted),
    name: z.string().min(1).max(128),
    label: z.string().min(1).max(160),
  }).strict(),
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.toolCompleted),
    name: z.string().min(1).max(128),
    success: z.literal(true),
    message: z.string().min(1).max(240),
  }).strict(),
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.toolFailed),
    name: z.string().min(1).max(128),
    success: z.literal(false),
    message: z.string().min(1).max(240),
  }).strict(),
  z.object({
    type: z.literal(LIVE_MESSAGE_TYPES.sessionError),
    code: z.string(),
    message: z.string(),
    reconnectable: z.boolean(),
  }),
  z.object({ type: z.literal(LIVE_MESSAGE_TYPES.sessionClosed) }),
]);

export const liveConnectionInfoSchema = z.object({
  webSocketUrl: z.string().regex(/^ws:\/\/127\.0\.0\.1:\d+\/ws\/live$/),
  bridgeToken: z.string().min(32),
});

export type LiveClientMessage = z.infer<typeof liveClientMessageSchema>;
export type LiveServerMessage = z.infer<typeof liveServerMessageSchema>;
export type LiveConnectionInfo = z.infer<typeof liveConnectionInfoSchema>;
