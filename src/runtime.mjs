import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

export function commandAvailable(command) {
  if (command.includes(path.sep)) return fs.existsSync(command) ? command : null;
  for (const directory of (process.env.PATH ?? "").split(path.delimiter)) {
    if (!directory) continue;
    const candidate = path.join(directory, command);
    try {
      const stat = fs.statSync(candidate);
      if (stat.isFile() && (process.platform === "win32" || (stat.mode & 0o111) !== 0)) return candidate;
    } catch {
      continue;
    }
  }
  return null;
}

export function runtimeAvailability(manifest) {
  return Object.fromEntries((manifest.runtime_commands ?? []).map((item) => [item.runtime, commandAvailable(item.command)]));
}

export function smokeRuntimes(manifest) {
  const results = [];
  for (const item of manifest.runtime_commands ?? []) {
    const executable = commandAvailable(item.command);
    if (!executable) {
      results.push({ runtime: item.runtime, command: item.command, status: "unverified", reason: item.install_recipe });
      continue;
    }
    const result = spawnSync(executable, ["--help"], { encoding: "utf8", timeout: 15000, env: { ...process.env, CI: "1" } });
    results.push({ runtime: item.runtime, command: executable, status: result.status === 0 ? "passed" : "failed", exit_code: result.status, output_sample: `${result.stdout ?? ""}${result.stderr ?? ""}`.slice(0, 500) });
  }
  return { generated_at: new Date().toISOString(), results, status: results.some((item) => item.status === "failed") ? "SMOKE_FAILED" : results.some((item) => item.status === "unverified") ? "SMOKE_PARTIAL" : "SMOKE_PASSED" };
}

export function bootstrapRuntimes(manifest) {
  const availability = runtimeAvailability(manifest);
  const results = (manifest.runtime_commands ?? []).map((item) => {
    const executable = availability[item.runtime];
    if (executable) return { runtime: item.runtime, status: "installed", action: "verify-existing", command: executable, verification: item.verification, install_recipe: item.install_recipe };
    const guiOnly = item.install_recipe.toLowerCase().includes("gui-dependent");
    return { runtime: item.runtime, status: guiOnly ? "unverified" : "missing", action: "report-only", command: item.command, verification: item.verification, install_recipe: item.install_recipe };
  });
  return { generated_at: new Date().toISOString(), results, status: results.some((item) => item.status === "missing") ? "BOOTSTRAP_NEEDS_MANUAL_INSTALL" : results.some((item) => item.status === "unverified") ? "BOOTSTRAP_PARTIAL" : "BOOTSTRAP_READY" };
}
