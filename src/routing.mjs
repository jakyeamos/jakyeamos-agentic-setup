export function detectRouteCycle(routes) {
  const adjacency = new Map();
  for (const route of routes) {
    if (!adjacency.has(route.from)) adjacency.set(route.from, []);
    adjacency.get(route.from).push(route.to);
  }
  const visiting = new Set();
  const visited = new Set();
  const stack = [];
  function visit(node) {
    if (visiting.has(node)) return [...stack.slice(stack.indexOf(node)), node];
    if (visited.has(node)) return [];
    visiting.add(node);
    stack.push(node);
    for (const next of adjacency.get(node) ?? []) {
      const cycle = visit(next);
      if (cycle.length > 0) return cycle;
    }
    stack.pop();
    visiting.delete(node);
    visited.add(node);
    return [];
  }
  for (const node of adjacency.keys()) {
    const cycle = visit(node);
    if (cycle.length > 0) return cycle;
  }
  return [];
}

export function lintAlwaysLoaded(content) {
  const lines = content.split(/\r?\n/);
  const findings = [];
  const pointerPattern = /\b(read|load|route|when|only|follow|context|on[- ]demand|see|manifest|adapter|pointer)\b/i;
  if (!pointerPattern.test(content)) findings.push({ severity: "error", code: "missing-router-pointer", message: "always-loaded file has no obvious route or load pointer" });
  if (/(?:^|\n)\s*```/.test(content)) findings.push({ severity: "error", code: "embedded-procedure", message: "code fence suggests a detailed procedure in an always-loaded file" });
  if (lines.some((line) => /^\s*(?:\d+\.|[-*])\s+(?:run|install|copy|execute|commit|push|pnpm|npm|node|brew|bash|git)\b/i.test(line))) findings.push({ severity: "error", code: "embedded-command-procedure", message: "always-loaded file contains command-bearing procedure steps" });
  if (/(?:^|\n)\s*@(?:\.\.?\/|~\/|\/)/.test(content)) findings.push({ severity: "error", code: "runtime-import-syntax", message: "runtime import syntax is present; keep it isolated to the adapter edge" });
  if (/\/(?:Users|private|var\/folders)\//.test(content)) findings.push({ severity: "error", code: "host-specific-path", message: "always-loaded file contains a host-specific absolute path" });
  return { line_count: lines.length, findings };
}
