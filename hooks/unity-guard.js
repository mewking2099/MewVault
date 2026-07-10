#!/usr/bin/env node
'use strict';
// unity-guard.js — enforces the hybrid Unity contract (read-only editor access).
//
// Registered as PreToolUse with matcher "mcp__.*[Uu]nity" (any Unity MCP bridge).
// Read tools pass; mutation tools are blocked with instructions to hand the
// user manual editor steps instead. This is what keeps "MewVault codes, the
// user drives the editor and learns" true under time pressure.
//
// Override for a session (owner decision): MEW_UNITY_WRITE=1

const fs = require('fs');

function readStdin() {
  try { return JSON.parse(fs.readFileSync(0, 'utf8')); } catch { return {}; }
}

// Tool-name fragments that indicate a READ (allowed). Everything else on a
// Unity MCP is treated as a mutation (blocked) — safe-by-default.
const READ_HINTS = [
  'read', 'get', 'list', 'find', 'query', 'inspect', 'search',
  'console', 'log', 'hierarchy', 'screenshot', 'state', 'status',
  'run_test', 'runtests', 'test_result', 'ping', 'info', 'select',
];

// Explicit mutation verbs — checked first so names like "get_or_create" block.
const WRITE_HINTS = [
  'create', 'add', 'set', 'delete', 'remove', 'destroy', 'instantiate',
  'move', 'rename', 'modify', 'update', 'write', 'apply', 'build',
  'save', 'import', 'execute_menu', 'menu_item', 'undo', 'redo', 'manage',
];

function main() {
  if (process.env.MEW_UNITY_WRITE === '1') process.exit(0);

  const input = readStdin();
  const tool = (input.tool_name || '').toLowerCase();
  if (!tool.includes('unity')) process.exit(0); // matcher safety net

  const isWrite = WRITE_HINTS.some(h => tool.includes(h));
  const isRead = !isWrite && READ_HINTS.some(h => tool.includes(h));

  if (isRead) process.exit(0);

  // Unknown or write tool → block (safe by default)
  process.stderr.write(
    `⛔ Unity guard: '${input.tool_name}' would modify the editor. The hybrid contract ` +
    `says the user performs ALL editor work by hand (that's how they learn).\n` +
    `Instead: give a numbered manual step — exact UI path, what to verify, and a ` +
    `"Why:" explainer — then wait for confirmation. Read tools (console, hierarchy, ` +
    `tests) remain available.\n` +
    `Session override (owner only): MEW_UNITY_WRITE=1\n`
  );
  process.exit(2);
}

main();
