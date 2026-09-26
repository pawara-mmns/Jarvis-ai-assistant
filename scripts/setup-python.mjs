import { existsSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const venvDirectory = join(root, ".venv");
const venvPython = join(venvDirectory, process.platform === "win32" ? "Scripts" : "bin", process.platform === "win32" ? "python.exe" : "python");

function run(executable, args) {
  const result = spawnSync(executable, args, { cwd: root, stdio: "inherit" });
  if (result.error || result.status !== 0) {
    console.error(result.error?.message ?? `Command exited with status ${result.status}`);
    process.exit(result.status ?? 1);
  }
}

if (!existsSync(venvPython)) {
  const executable = process.env.JARVIS_PYTHON_PATH ?? (process.platform === "win32" ? "py" : "python3");
  const prefix = !process.env.JARVIS_PYTHON_PATH && process.platform === "win32" ? ["-3.12"] : [];
  run(executable, [...prefix, "-m", "venv", venvDirectory]);
}

run(venvPython, ["-m", "pip", "install", "--upgrade", "pip"]);
run(venvPython, ["-m", "pip", "install", "-r", "requirements.txt"]);
