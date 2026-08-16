import { execFileSync } from "node:child_process";
import { existsSync, lstatSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateAgentUsability } from "./check_agent_usability.mjs";

const DEFAULT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PACKETS = [
  "architecture.md",
  "commands.md",
  "conventions.md",
  "security.md",
  "failure-modes.md",
  "examples.md",
  "done.md",
  "deployment.md"
];
const QUALITY_COMMANDS = [
  "pnpm lint",
  "pnpm typecheck",
  "pnpm test",
  "pnpm build",
  "pnpm check",
  "python3 scripts/pre_cr_coverage.py"
];
const REQUIRED_SCRIPTS = {
  test: "node --test",
  lint: "python3 scripts/validate_repository.py",
  typecheck: "node scripts/check_javascript.mjs",
  build: "python3 scripts/validate_catalog.py",
  check: "node scripts/check_environment_contract.mjs"
};
const REQUIRED_IGNORES = [
  ".env",
  ".env.*",
  "node_modules/",
  ".pre-cr/",
  "audit/",
  ".aios/",
  ".quality-runner/"
];
const REVIEW_PATTERN = /last_reviewed:\s*(\d{4}-\d{2}-\d{2})/;
const LINK_PATTERN = /\[[^\]]+\]\(([^)]+)\)/g;
const SECRET_NAME_PATTERN = /(^|\/)(?:\.env(?:\..*)?|.*\.(?:pem|key|p12|pfx)|id_rsa|credentials(?:\.[^/]+)?)$/i;
const SAFE_SECRET_NAMES = new Set([".env.example", ".env.template"]);
const DAY_MS = 24 * 60 * 60 * 1000;

// A dimension-only report is still evidence-bearing: freshness must retain the
// measured age and its limit rather than collapsing to a bare pass/fail value.

function readJson(file) {
  return JSON.parse(readFileSync(file, "utf8"));
}

function pathInside(root, target) {
  const relative = path.relative(root, target);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== "..");
}

function dateOnly(value) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
}

export function freshnessEvidence(reviewedInput, asOfInput, limitDays = 35) {
  const reviewed = dateOnly(reviewedInput);
  const asOf = dateOnly(asOfInput);
  if (reviewed === null || asOf === null) {
    return { status: "unknown", age_days: null, limit_days: limitDays };
  }
  const ageDays = Math.floor((asOf - reviewed) / DAY_MS);
  return {
    status: ageDays > limitDays ? "fail" : "pass",
    age_days: ageDays,
    limit_days: limitDays
  };
}

export function summarizeDimensionStatuses(result) {
  const checks = result?.checks ?? {};
  const context = checks.context_dimensions ?? {};
  const freshness = context.freshness_evidence ?? {};
  const statusOf = (value) => (typeof value === "string" ? value : "unknown");
  const nestedStatuses = (value) => Object.fromEntries(
    Object.entries(value ?? {}).map(([key, item]) => [
      key,
      statusOf(item?.status)
    ])
  );
  return {
    ownership: statusOf(context.ownership),
    freshness: {
      status: statusOf(context.freshness ?? freshness.status),
      age_days: typeof freshness.age_days === "number" ? freshness.age_days : null,
      limit_days: typeof freshness.limit_days === "number" ? freshness.limit_days : null
    },
    links: statusOf(context.links),
    package_manager: statusOf(checks.package_manager?.status),
    quality_gates: nestedStatuses(checks.quality_gates),
    ignore_rules: nestedStatuses(checks.ignore_rules),
    tracked_secret_custody: statusOf(checks.tracked_secret_custody)
  };
}

function trackedPaths(root) {
  try {
    return execFileSync("git", ["ls-files", "-z"], { cwd: root, encoding: "utf8" })
      .split("\0")
      .filter(Boolean);
  } catch {
    return null;
  }
}

function checkContext(root, errors, asOf) {
  const indexPath = path.join(root, ".agents", "context", "README.md");
  if (!existsSync(indexPath)) {
    errors.push("missing .agents/context/README.md");
    return;
  }
  if (lstatSync(indexPath).isSymbolicLink()) errors.push("context index must not be a symlink");
  const text = readFileSync(indexPath, "utf8");
  const reviewed = text.match(REVIEW_PATTERN);
  if (!reviewed) {
    errors.push("context index is missing last_reviewed");
  } else {
    const reviewedDate = dateOnly(`${reviewed[1]}T00:00:00Z`);
    if (reviewedDate === null || asOf === null) {
      errors.push("context index has an invalid freshness date");
    } else if (freshnessEvidence(reviewedDate, asOf).status === "fail") {
      errors.push(`context index is stale: ${reviewed[1]}`);
    }
  }
  for (const match of text.matchAll(LINK_PATTERN)) {
    const link = match[1].split("#", 1)[0];
    if (!link || link.startsWith("#") || /^[a-z][a-z0-9+.-]*:/i.test(link)) continue;
    const target = path.resolve(path.dirname(indexPath), link);
    if (!pathInside(root, target) || !existsSync(target) || !lstatSync(target).isFile()) {
      errors.push(`broken context link: ${link}`);
    }
  }
  for (const packet of PACKETS) {
    const packetPath = path.join(path.dirname(indexPath), packet);
    if (!existsSync(packetPath)) {
      errors.push(`missing context packet: ${packet}`);
    } else if (lstatSync(packetPath).isSymbolicLink()) {
      errors.push(`context packet must not be a symlink: ${packet}`);
    }
  }
}

export function validateContract(rootInput = DEFAULT_ROOT, asOfInput = new Date(), paths = null) {
  const root = path.resolve(rootInput);
  const errors = [];
  const asOf = dateOnly(asOfInput);
  if (asOf === null) errors.push("invalid --as-of date");
  for (const required of ["AGENTS.md", "README.md", "SECURITY.md", "package.json", "catalog/manifest.json", "catalog/taxonomy.json", "library/README.md", ".agents/agent-usability.json", "scripts/validate_repository.py", "scripts/check_agent_usability.mjs", "scripts/check_javascript.mjs"]) {
    if (!existsSync(path.join(root, required))) errors.push(`missing required surface: ${required}`);
  }
  checkContext(root, errors, asOf);
  const agentUsability = validateAgentUsability(root);
  errors.push(...agentUsability.errors);

  try {
    const packageJson = readJson(path.join(root, "package.json"));
    for (const [name, command] of Object.entries(REQUIRED_SCRIPTS)) {
      if (packageJson.scripts?.[name] !== command) errors.push(`package script drift: ${name}`);
    }
    if (packageJson.packageManager !== "pnpm@11.9.0") errors.push("packageManager must pin pnpm@11.9.0");
  } catch (error) {
    errors.push(`invalid package.json: ${error.message}`);
  }

  try {
    const preCr = readJson(path.join(root, ".pre-cr.json"));
    if (JSON.stringify(preCr.qualityCommands) !== JSON.stringify(QUALITY_COMMANDS)) {
      errors.push(".pre-cr.json qualityCommands drift");
    }
    const adapter = (preCr.qualityAdapters ?? []).find((item) => item?.name === "environment-contract");
    if (adapter?.required !== true || adapter.command !== "node scripts/check_environment_contract.mjs") {
      errors.push("required environment-contract quality adapter is missing or drifted");
    }
  } catch (error) {
    errors.push(`invalid .pre-cr.json: ${error.message}`);
  }

  try {
    const gitignore = readFileSync(path.join(root, ".gitignore"), "utf8");
    for (const entry of REQUIRED_IGNORES) {
      if (!gitignore.split(/\r?\n/).some((line) => line.trim() === entry)) errors.push(`missing .gitignore rule: ${entry}`);
    }
  } catch (error) {
    errors.push(`unable to read .gitignore: ${error.message}`);
  }

  const tracked = paths ?? trackedPaths(root);
  if (tracked === null) {
    errors.push("git tracked-path inspection unavailable");
  } else {
    for (const file of tracked) {
      const basename = path.basename(file).toLowerCase();
      if (SAFE_SECRET_NAMES.has(basename)) continue;
      if (SECRET_NAME_PATTERN.test(file)) errors.push(`secret-like tracked path: ${file}`);
    }
  }
  const contextErrors = errors.filter((error) =>
    error.startsWith("missing .agents/context/") ||
    error.startsWith("context index") ||
    error.startsWith("context packet") ||
    error.startsWith("broken context link")
  );
  const contextIndex = path.join(root, ".agents", "context", "README.md");
  let contextFreshnessDays = null;
  if (existsSync(contextIndex) && !lstatSync(contextIndex).isSymbolicLink()) {
    const reviewed = readFileSync(contextIndex, "utf8").match(REVIEW_PATTERN);
    if (reviewed && asOf !== null) {
      const reviewedDate = dateOnly(`${reviewed[1]}T00:00:00Z`);
      if (reviewedDate !== null) {
        contextFreshnessDays = freshnessEvidence(reviewedDate, asOf).age_days;
      }
    }
  }
  const reviewedValue = existsSync(contextIndex) && !lstatSync(contextIndex).isSymbolicLink()
    ? readFileSync(contextIndex, "utf8").match(REVIEW_PATTERN)?.[1]
    : null;
  const measuredFreshness = freshnessEvidence(reviewedValue, asOf, 35);
  const freshnessStatus = contextErrors.some((error) => error.startsWith("context index"))
    ? "fail"
    : measuredFreshness.status;
  const contextDimensions = {
    ownership: contextErrors.some((error) => error.includes("must not be a symlink") || error.includes("missing .agents/context/README.md")) ? "fail" : "pass",
    freshness: freshnessStatus,
    freshness_evidence: {
      ...measuredFreshness,
      status: freshnessStatus
    },
    links: contextErrors.some((error) => error.startsWith("broken context link")) ? "fail" : "pass",
    freshness_days: contextFreshnessDays,
    freshness_limit_days: 35
  };
  const qualityGateChecks = Object.fromEntries(
    Object.entries(REQUIRED_SCRIPTS).map(([name, command]) => [
      name,
      {
        command,
        status: errors.includes(`package script drift: ${name}`) ? "fail" : "pass"
      }
    ])
  );
  const ignoreRuleChecks = Object.fromEntries(
    REQUIRED_IGNORES.map((rule) => [
      rule,
      {
        status: errors.includes(`missing .gitignore rule: ${rule}`) ? "fail" : "pass"
      }
    ])
  );
  const packageManager = (() => {
    try {
      const packageJson = readJson(path.join(root, "package.json"));
      const value = packageJson.packageManager ?? null;
      return {
        value,
        expected: "pnpm@11.9.0",
        status: value === "pnpm@11.9.0" ? "pass" : "fail"
      };
    } catch {
      return { value: null, expected: "pnpm@11.9.0", status: "unknown" };
    }
  })();
  return {
    schema_version: "environment-contract/v1",
    as_of: new Date(asOfInput).toISOString(),
    status: errors.length === 0 ? "pass" : "fail",
    errors: [...new Set(errors)].sort(),
    checks: {
      context_packets: PACKETS.filter((packet) => existsSync(path.join(root, ".agents/context", packet))).length,
      context_packets_required: PACKETS.length,
      context_dimensions: contextDimensions,
      package_manager: packageManager,
      quality_gates: qualityGateChecks,
      ignore_rules: ignoreRuleChecks,
      quality_commands: QUALITY_COMMANDS.length,
      tracked_secret_paths: errors.filter((error) => error.startsWith("secret-like tracked path:")).length,
      tracked_secret_custody: errors.some((error) => error.startsWith("secret-like tracked path:")) ? "fail" : "pass",
      strict_javascript_syntax: true,
      required_pre_cr_adapter: !errors.some((error) => error.includes("quality adapter")),
      agent_usability: agentUsability
    }
  };
}

function parseArguments(argv) {
  const options = { root: DEFAULT_ROOT, asOf: new Date() };
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--root") options.root = argv[++index];
    else if (argv[index] === "--as-of") options.asOf = argv[++index];
    else throw new Error(`unknown argument: ${argv[index]}`);
  }
  return options;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const options = parseArguments(process.argv.slice(2));
    const result = validateContract(options.root, options.asOf);
    console.log(JSON.stringify(result, null, 2));
    process.exitCode = result.status === "pass" ? 0 : 1;
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
