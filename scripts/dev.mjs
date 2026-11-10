// One development command; Python remains in the active Conda/venv environment.
import { spawn } from "node:child_process";
import { createServer } from "node:net";

const port = Number(process.env.BACKEND_PORT || 8000);
if (!Number.isInteger(port) || port < 1 || port > 65535) {
  console.error("BACKEND_PORT must be between 1 and 65535.");
  process.exit(1);
}
const children = new Set();
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) child.kill("SIGTERM");
  process.exitCode = code;
}
function start(command, args, env = process.env) {
  const child = spawn(command, args, { stdio: "inherit", env });
  children.add(child);
  child.on("error", () => {
    console.error(
      `Could not start ${command}. Activate the project Python environment first.`,
    );
    stop(1);
  });
  child.on("exit", (code) => {
    children.delete(child);
    if (!stopping) stop(code || 0);
  });
  return child;
}
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => stop());

try {
  await new Promise((resolve, reject) => {
    const probe = createServer();
    probe.once("error", () =>
      reject(
        new Error(
          `Port ${port} is already occupied. Stop the old server or use BACKEND_PORT=${port + 1} npm run dev.`,
        ),
      ),
    );
    probe.listen(port, "127.0.0.1", () => probe.close(resolve));
  });
  const python = start(process.env.BERTOPIC_PYTHON || "python", [
    "-m",
    "uvicorn",
    "server.app:app",
    "--host",
    "127.0.0.1",
    "--port",
    String(port),
  ]);
  console.log("Starting Python API…");
  const deadline = Date.now() + 120_000;
  let ready = false;
  while (!stopping && Date.now() < deadline) {
    if (python.exitCode !== null) break;
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/health`);
      if (response.ok) {
        ready = true;
        break;
      }
    } catch {
      /* wait for Python imports to complete */
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  if (!stopping) {
    if (!ready)
      throw new Error(
        "The Python API did not become ready. Check the error above.",
      );
    start(
      process.execPath,
      ["node_modules/vite/bin/vite.js", "--host", "127.0.0.1"],
      { ...process.env, BACKEND_PORT: String(port) },
    );
  }
} catch (error) {
  console.error(error.message);
  stop(1);
}
