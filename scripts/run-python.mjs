import { existsSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const venvPython = join(root, ".venv", process.platform === "win32" ? "Scripts" : "bin", process.platform === "win32" ? "python.exe" : "python");

let executable;
let prefix = [];
if (existsSync(venvPython)) {
  executable = venvPython;
} else if (process.env.JARVIS_PYTHON_PATH) {
  executable = process.env.JARVIS_PYTHON_PATH;
} else if (process.platform === "win32") {
  executable = "py";
  prefix = ["-3.12"];
} else {
  executable = "python3";
}

const result = spawnSync(executable, [...prefix, ...process.argv.slice(2)], {
  cwd: root,
  env: process.env,
  stdio: "inherit",
});

if (result.error) {
  console.error(`Unable to start Python: ${result.error.message}`);
  console.error("Run npm run python:setup or set JARVIS_PYTHON_PATH.");
  process.exit(1);
}

process.exit(result.status ?? 1);
