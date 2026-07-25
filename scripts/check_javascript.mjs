import { execFileSync } from "node:child_process";
import { readdirSync, lstatSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE_DIRECTORIES = ["bin", "src", "scripts", "test"];
const SKIP_DIRECTORIES = new Set([".git", "node_modules", ".pre-cr", "audit"]);

function javascriptFiles(directory) {
  const files = [];
  for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a, b) =>
    a.name.localeCompare(b.name)
  )) {
    if (SKIP_DIRECTORIES.has(entry.name)) continue;
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...javascriptFiles(target));
    } else if (entry.isFile() && [".js", ".mjs"].includes(path.extname(entry.name))) {
      files.push(target);
    }
  }
  return files;
}

for (const directory of SOURCE_DIRECTORIES) {
  const target = path.join(ROOT, directory);
  if (lstatSync(target).isDirectory()) {
    for (const file of javascriptFiles(target)) {
      execFileSync(process.execPath, ["--check", file], { stdio: "inherit" });
    }
  }
}

console.log("javascript syntax check ok");
