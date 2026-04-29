#!/usr/bin/env node
/**
 * sync-runs.js — copies real-run JSONs from `../runs/` (repo root) into
 * `frontend/public/runs/` so Vite can serve them at /runs/*.json and
 * `import.meta.glob` can pick them up at build time.
 *
 * Runs automatically before `dev` and `build` via the `predev` / `prebuild`
 * scripts in package.json.
 *
 * Idempotent: clears `public/runs/` first, then re-copies. Silent (just a
 * count log) when there are no JSONs — that's the normal state until the
 * Python engine starts producing runs.
 */
import { mkdirSync, readdirSync, copyFileSync, rmSync, existsSync, statSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FRONTEND_ROOT = resolve(__dirname, "..");
const REPO_ROOT = resolve(FRONTEND_ROOT, "..");
const SRC_DIR = join(REPO_ROOT, "runs");
const DEST_DIR = join(FRONTEND_ROOT, "public", "runs");

function main() {
  // Reset destination
  if (existsSync(DEST_DIR)) rmSync(DEST_DIR, { recursive: true, force: true });
  mkdirSync(DEST_DIR, { recursive: true });

  if (!existsSync(SRC_DIR) || !statSync(SRC_DIR).isDirectory()) {
    console.log(`[sync-runs] No ${SRC_DIR} directory — frontend will use mock data.`);
    return;
  }

  const files = readdirSync(SRC_DIR).filter(f => f.endsWith(".json"));
  if (files.length === 0) {
    console.log(`[sync-runs] ${SRC_DIR} is empty — frontend will use mock data.`);
    return;
  }

  for (const f of files) {
    copyFileSync(join(SRC_DIR, f), join(DEST_DIR, f));
  }
  console.log(`[sync-runs] Copied ${files.length} run JSON(s) → public/runs/`);
}

try {
  main();
} catch (err) {
  console.error("[sync-runs] Failed:", err);
  process.exit(0); // never block dev/build — just fall back to mock
}
