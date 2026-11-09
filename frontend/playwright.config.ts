import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 90000,
  use: {
    baseURL: "http://127.0.0.1:5173",
    viewport: { width: 1440, height: 1000 },
    launchOptions: {
      executablePath:
        process.env.CHROMIUM_PATH ||
        (existsSync("/usr/bin/chromium") ? "/usr/bin/chromium" : undefined),
      args: ["--no-sandbox"],
    },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `${process.env.BERTOPIC_PYTHON || "python"} -m tests_web.serve_e2e`,
      cwd: "..",
      url: "http://127.0.0.1:8000/api/health",
      timeout: 180000,
      reuseExistingServer: false,
      env: {
        HF_HUB_OFFLINE: "1",
        OMP_NUM_THREADS: "2",
        NUMBA_NUM_THREADS: "2",
      },
    },
    {
      command: "npm run dev -- --port 5173",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
    },
  ],
});
