// Vercel build: website ki static files ko har sambhav output jagah par rakhta hai, taaki Vercel ka
// Root Directory (repo root ya dashboard) aur entrypoint kuch bhi chune, "public" folder mil jaaye.
// Koi npm dependency nahi. Build log mein sirf non-secret jaankari chhapta hai.
import { cpSync, existsSync, readdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url)); // .../dashboard
const src = join(here, "public");
const repoRoot = resolve(here, "..");

if (!existsSync(join(src, "index.html"))) {
  console.error(`[bot-dashboard] FAIL: ${src}/index.html nahi mila`);
  process.exit(1);
}

const targets = new Set([join(repoRoot, "public"), resolve(process.cwd(), "public")]);
for (const t of targets) {
  if (resolve(t) === resolve(src)) continue;
  rmSync(t, { recursive: true, force: true });
  cpSync(src, t, { recursive: true });
}

const safeEnv = Object.fromEntries(
  Object.entries(process.env).filter(
    ([k]) => k === "VERCEL_ENV" || k === "VERCEL_GIT_COMMIT_REF" || k.startsWith("VERCEL_PROJECT_SETTINGS_"),
  ),
);
console.log("[bot-dashboard] build ok");
console.log(`[bot-dashboard] cwd=${process.cwd()} dashboard=${here} node=${process.version}`);
console.log(`[bot-dashboard] files: ${readdirSync(src).join(", ")}`);
console.log(`[bot-dashboard] output folders: ${[src, ...targets].filter((t) => existsSync(t)).join(" | ")}`);
console.log(`[bot-dashboard] settings: ${JSON.stringify(safeEnv)}`);
