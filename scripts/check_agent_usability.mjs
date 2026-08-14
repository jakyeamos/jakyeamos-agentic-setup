import { existsSync, lstatSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CONTRACT_RELATIVE_PATH = ".agents/agent-usability.json";
const VALID_APPLICABILITY = new Set(["applicable", "not-applicable"]);

function readJson(file) {
  return JSON.parse(readFileSync(file, "utf8"));
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function pathInside(root, target) {
  const relative = path.relative(root, target);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== "..");
}

function evidencePath(root, rawPath) {
  if (typeof rawPath !== "string" || rawPath.trim() === "") return null;
  if (path.isAbsolute(rawPath) || rawPath.startsWith("~")) return null;
  const target = path.resolve(root, rawPath);
  if (!pathInside(root, target)) return null;
  return target;
}

function hasEvidenceFile(root, entry) {
  if (!isObject(entry)) return false;
  const target = evidencePath(root, entry.path);
  return target !== null && existsSync(target) && lstatSync(target).isFile();
}

function validateEvidenceEntry(root, toolId, entry, index, errors) {
  if (!isObject(entry)) {
    errors.push(`agent-usability tool ${toolId}: behavior evidence ${index + 1} must be an object`);
    return false;
  }

  const target = evidencePath(root, entry.path);
  if (target === null) {
    errors.push(`agent-usability tool ${toolId}: behavior evidence ${index + 1} path must be a relative in-repository file`);
    return false;
  }
  if (!existsSync(target) || !lstatSync(target).isFile()) {
    errors.push(`agent-usability tool ${toolId}: missing behavior evidence ${entry.path}`);
    return false;
  }
  return true;
}

export function validateAgentUsability(rootInput = DEFAULT_ROOT) {
  const root = path.resolve(rootInput);
  const contractPath = path.join(root, CONTRACT_RELATIVE_PATH);
  const errors = [];
  let contract = null;

  if (!existsSync(contractPath)) {
    errors.push(`missing agent usability contract: ${CONTRACT_RELATIVE_PATH}`);
  } else if (lstatSync(contractPath).isSymbolicLink()) {
    errors.push(`agent usability contract must not be a symlink: ${CONTRACT_RELATIVE_PATH}`);
  } else {
    try {
      contract = readJson(contractPath);
    } catch (error) {
      errors.push(`invalid agent usability contract: ${error.message}`);
    }
  }

  if (!isObject(contract)) {
    if (contract !== null) errors.push("agent usability contract must be a JSON object");
  } else {
    if (contract.schema !== "agent-usability/v1") {
      errors.push("agent usability contract schema must be agent-usability/v1");
    }

    const applicability = contract.applicability;
    if (!VALID_APPLICABILITY.has(applicability)) {
      errors.push("agent usability contract applicability must be applicable or not-applicable");
    }
    if (applicability === "not-applicable" &&
        (typeof contract.reason !== "string" || contract.reason.trim() === "")) {
      errors.push('agent usability contract: not-applicable requires a non-empty reason');
    }

    const tools = contract.tools;
    if (!Array.isArray(tools)) {
      errors.push("agent usability contract tools must be an array");
    } else {
      if (applicability === "applicable" && tools.length === 0) {
        errors.push('agent usability contract: applicability "applicable" requires at least one declared tool');
      }

      const toolIds = new Set();
      for (const [index, tool] of tools.entries()) {
        if (!isObject(tool)) {
          errors.push(`agent-usability tool ${index + 1}: tool declaration must be an object`);
          continue;
        }

        const hasToolId = typeof tool.id === "string" && tool.id.trim() !== "";
        const toolId = hasToolId ? tool.id : `#${index + 1}`;
        if (!hasToolId) errors.push(`agent-usability tool ${toolId}: id must be a non-empty string`);
        if (toolIds.has(toolId)) errors.push(`agent-usability tool ${toolId}: duplicate tool id`);
        toolIds.add(toolId);

        if (!Array.isArray(tool.behavior_evidence)) {
          errors.push(`agent-usability tool ${toolId}: behavior_evidence must be an array`);
          continue;
        }

        const validEvidence = tool.behavior_evidence.reduce(
          (count, entry, entryIndex) =>
            count + (validateEvidenceEntry(root, toolId, entry, entryIndex, errors) ? 1 : 0),
          0
        );
        if (applicability === "applicable" && validEvidence === 0) {
          errors.push(`agent-usability tool ${toolId}: no behavior evidence declared`);
        }
      }
    }
  }

  const tools = Array.isArray(contract?.tools) ? contract.tools : [];
  const toolsWithBehaviorEvidence = tools.filter(
    (tool) =>
      isObject(tool) &&
      Array.isArray(tool.behavior_evidence) &&
      tool.behavior_evidence.some((entry) => hasEvidenceFile(root, entry))
  ).length;

  return {
    schema_version: "agent-usability-check/v1",
    contract_path: CONTRACT_RELATIVE_PATH,
    status: errors.length === 0 ? "pass" : "fail",
    errors: [...new Set(errors)].sort(),
    checks: {
      applicability: typeof contract?.applicability === "string" ? contract.applicability : null,
      declared_tools: tools.length,
      tools_with_behavior_evidence: toolsWithBehaviorEvidence
    }
  };
}

function parseArguments(argv) {
  const options = { root: DEFAULT_ROOT };
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--root") options.root = argv[++index];
    else throw new Error(`unknown argument: ${argv[index]}`);
  }
  return options;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const options = parseArguments(process.argv.slice(2));
    const result = validateAgentUsability(options.root);
    console.log(JSON.stringify(result, null, 2));
    process.exitCode = result.status === "pass" ? 0 : 1;
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
