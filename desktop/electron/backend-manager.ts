import { existsSync } from "node:fs";
import { randomBytes } from "node:crypto";
import { join } from "node:path";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { backendHealthSchema, type BackendHealth } from "../../shared/schemas/health";

const LOOPBACK_HOST = "127.0.0.1";
const DEFAULT_PORT = 8765;
const STARTUP_TIMEOUT_MS = 12_000;
const SHUTDOWN_TIMEOUT_MS = 3_000;

type BackendStatus = "stopped" | "starting" | "ready" | "failed";

interface PythonCommand {
  executable: string;
  args: string[];
}

function parsePort(value: string | undefined): number {
  const port = Number(value ?? DEFAULT_PORT);
  return Number.isInteger(port) && port >= 1024 && port <= 65535 ? port : DEFAULT_PORT;
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export class BackendManager {
  private process: ChildProcessWithoutNullStreams | null = null;
  private startPromise: Promise<void> | null = null;
  private status: BackendStatus = "stopped";
  private readonly port = parsePort(process.env.JARVIS_AGENT_PORT);
  private readonly liveBridgeToken = randomBytes(32).toString("hex");

  constructor(
    private readonly projectRoot: string,
    private readonly expectedVersion?: string,
  ) {}

  get currentStatus(): BackendStatus {
    return this.status;
  }

  get liveWebSocketUrl(): string {
    return `ws://${LOOPBACK_HOST}:${this.port}/ws/live`;
  }

  get bridgeToken(): string {
    return this.liveBridgeToken;
  }

  async start(): Promise<void> {
    if (this.process && !this.process.killed) {
      return this.startPromise ?? Promise.resolve();
    }
    if (this.startPromise) {
      return this.startPromise;
    }

    this.startPromise = this.startInternal();
    try {
      await this.startPromise;
    } finally {
      this.startPromise = null;
    }
  }

  async getHealth(): Promise<BackendHealth> {
    const response = await fetch(`http://${LOOPBACK_HOST}:${this.port}/health`, {
      signal: AbortSignal.timeout(2_000),
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Agent health request failed with status ${response.status}`);
    }

    const health = backendHealthSchema.parse(await response.json());
    if (this.expectedVersion && health.version !== this.expectedVersion) {
      throw new Error(
        `Agent version mismatch: expected ${this.expectedVersion}, received ${health.version}`,
      );
    }
    return health;
  }

  async stop(): Promise<void> {
    const child = this.process;
    if (!child) {
      this.status = "stopped";
      return;
    }

    console.info("[desktop] stopping agent", { pid: child.pid });
    const exited = new Promise<boolean>((resolve) => {
      const timeout = setTimeout(() => resolve(false), SHUTDOWN_TIMEOUT_MS);
      child.once("exit", () => {
        clearTimeout(timeout);
        resolve(true);
      });
    });

    child.stdin.end();
    if (!(await exited) && child.pid) {
      console.warn("[desktop] forcing agent shutdown", { pid: child.pid });
      await this.forceStop(child.pid);
    }

    this.process = null;
    this.status = "stopped";
    console.info("[desktop] agent stopped");
  }

  private async startInternal(): Promise<void> {
    this.status = "starting";
    const command = this.resolvePythonCommand();
    console.info("[desktop] starting agent", { executable: command.executable, port: this.port });

    const child = spawn(command.executable, [...command.args, "-m", "agent.main"], {
      cwd: this.projectRoot,
      env: {
        ...process.env,
        JARVIS_AGENT_HOST: LOOPBACK_HOST,
        JARVIS_AGENT_PORT: String(this.port),
        JARVIS_LIVE_TOKEN: this.liveBridgeToken,
        PYTHONUNBUFFERED: "1",
      },
      windowsHide: true,
      stdio: "pipe",
    });
    this.process = child;

    child.stdout.on("data", (data: Buffer) => {
      const message = data.toString().trim();
      if (message) console.info(`[agent] ${message}`);
    });
    child.stderr.on("data", (data: Buffer) => {
      const message = data.toString().trim();
      if (message) console.error(`[agent] ${message}`);
    });
    child.once("error", (error) => {
      this.status = "failed";
      console.error("[desktop] agent process error", error);
    });
    child.once("exit", (code, signal) => {
      if (this.process === child) {
        this.process = null;
        if (this.status !== "stopped") this.status = code === 0 ? "stopped" : "failed";
      }
      console.info("[desktop] agent exited", { code, signal });
    });

    const deadline = Date.now() + STARTUP_TIMEOUT_MS;
    while (Date.now() < deadline) {
      if (child.exitCode !== null) break;
      try {
        await this.getHealth();
        this.status = "ready";
        console.info("[desktop] agent ready", { url: `http://${LOOPBACK_HOST}:${this.port}` });
        return;
      } catch {
        await wait(250);
      }
    }

    this.status = "failed";
    await this.stop();
    throw new Error("Agent did not become healthy before the startup timeout");
  }

  private resolvePythonCommand(): PythonCommand {
    const configured = process.env.JARVIS_PYTHON_PATH;
    if (configured) return { executable: configured, args: [] };

    const venvExecutable = join(
      this.projectRoot,
      ".venv",
      process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
    );
    if (existsSync(venvExecutable)) return { executable: venvExecutable, args: [] };

    if (process.platform === "win32") return { executable: "py", args: ["-3.12"] };
    return { executable: "python3", args: [] };
  }

  private async forceStop(pid: number): Promise<void> {
    if (process.platform !== "win32") {
      this.process?.kill("SIGKILL");
      return;
    }

    await new Promise<void>((resolve) => {
      const killer = spawn("taskkill", ["/pid", String(pid), "/T", "/F"], {
        windowsHide: true,
        stdio: "ignore",
      });
      killer.once("exit", () => resolve());
      killer.once("error", () => resolve());
    });
  }
}
