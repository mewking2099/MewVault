#!/usr/bin/env node
'use strict';
// agent-track.js — agent dispatch ledger + model gate.
//
// Registered twice:
//   PreToolUse  (matcher: Task)  — logs every Agent/Task dispatch; BLOCKS (exit 2)
//                                  mew-* agent dispatches missing the model param
//                                  (the silent-Sonnet-fallback problem in CLAUDE.md).
//   SubagentStop (matcher: "")   — logs completions.
//
// Ledger: <workspace>/.claude/agent-dispatches.jsonl (rotated at 500 KB).
// Read it with: mew agent status

const fs = require('fs');
const path = require('path');

const LEDGER_MAX_BYTES = 500 * 1024;

function readStdin() {
  try { return JSON.parse(fs.readFileSync(0, 'utf8')); } catch { return {}; }
}

function findWorkspaceRoot(startDir) {
  let dir = path.resolve(startDir);
  while (true) {
    if (fs.existsSync(path.join(dir, '.claude', 'rules', 'mew-common'))) return dir;
    if (fs.existsSync(path.join(dir, 'mewvault')) && fs.existsSync(path.join(dir, 'wiki'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) return startDir;
    dir = parent;
  }
}

function ledgerPath(workspaceRoot) {
  return path.join(workspaceRoot, '.claude', 'agent-dispatches.jsonl');
}

function appendLedger(workspaceRoot, entry) {
  const file = ledgerPath(workspaceRoot);
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    // Rotate: keep the newest half when the ledger exceeds the cap
    if (fs.existsSync(file) && fs.statSync(file).size > LEDGER_MAX_BYTES) {
      const lines = fs.readFileSync(file, 'utf8').trim().split('\n');
      fs.writeFileSync(file, lines.slice(Math.floor(lines.length / 2)).join('\n') + '\n', 'utf8');
    }
    fs.appendFileSync(file, JSON.stringify(entry) + '\n', 'utf8');
  } catch {}
}

function knownMewAgents(workspaceRoot) {
  // Agent definitions live in mewvault/.claude/agents/*.md (workspace .claude/agents/ as fallback)
  const mewvaultRoot = process.env.MEWVAULT_ROOT || path.join(__dirname, '..');
  const candidates = [
    path.join(mewvaultRoot, '.claude', 'agents'),
    path.join(workspaceRoot, 'mewvault', '.claude', 'agents'),
    path.join(workspaceRoot, '.claude', 'agents'),
  ];
  const names = new Set();
  for (const dir of candidates) {
    try {
      for (const f of fs.readdirSync(dir)) {
        if (f.endsWith('.md')) names.add(f.replace(/\.md$/, ''));
      }
    } catch {}
  }
  return names;
}

function main() {
  const input = readStdin();
  const cwd = input.cwd || process.cwd();
  const workspaceRoot = findWorkspaceRoot(cwd);
  const event = input.hook_event_name || '';
  const ts = new Date().toISOString();

  if (event === 'SubagentStop') {
    appendLedger(workspaceRoot, { ts, event: 'stop', session_id: input.session_id || '' });
    process.exit(0);
  }

  // PreToolUse on the Task tool
  const toolInput = input.tool_input || {};
  const agent = toolInput.subagent_type || 'general-purpose';
  const model = toolInput.model || null;
  const description = (toolInput.description || '').substring(0, 120);
  const isMewAgent = knownMewAgents(workspaceRoot).has(agent);

  // Model gate: mew agents must be dispatched with an explicit model param.
  if (isMewAgent && !model) {
    appendLedger(workspaceRoot, {
      ts, event: 'blocked', session_id: input.session_id || '',
      agent, description, reason: 'missing model param',
    });
    process.stderr.write(
      `BLOCKED: dispatch of ${agent} without a model param would silently fall back ` +
      `to the session default. Re-dispatch with the model from the CLAUDE.md ` +
      `"Model lookup table" (Agent dispatch — mandatory rules).\n`
    );
    process.exit(2); // exit 2 = block the tool call, stderr goes to Claude
  }

  appendLedger(workspaceRoot, {
    ts, event: 'dispatch', session_id: input.session_id || '',
    agent, model, description,
    prompt_chars: (toolInput.prompt || '').length,
  });
  process.exit(0);
}

main();
