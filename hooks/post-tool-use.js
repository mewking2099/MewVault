#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');
const { spawn } = require('child_process');

const GRAPHIFY_SOURCE_EXTS = new Set([
  '.py', '.js', '.ts', '.tsx', '.jsx', '.gd',
  '.rs', '.go', '.java', '.rb', '.c', '.h', '.cpp', '.cs', '.kt', '.swift',
]);

function findGraphifyRoot(startDir) {
  let dir = path.resolve(startDir);
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(dir, 'graphify-out', 'graph.json'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function runGraphifyUpdate(filePath, cwd) {
  const ext = path.extname(filePath).toLowerCase();
  if (!GRAPHIFY_SOURCE_EXTS.has(ext)) return;
  const searchBase = filePath ? path.dirname(path.resolve(filePath)) : cwd;
  const root = findGraphifyRoot(searchBase) || findGraphifyRoot(cwd);
  if (!root) return;
  const child = spawn('graphify', ['update', '.'], {
    cwd: root,
    detached: true,
    stdio: 'ignore',
  });
  child.unref();
}

const MEWVAULT_ROOT = process.env.MEWVAULT_ROOT || path.join(__dirname, '..');

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

function detectSilo(cwd, workspaceRoot) {
  const rel = path.relative(workspaceRoot, path.resolve(cwd)).replace(/\\/g, '/');
  if (rel.startsWith('wiki')) return 'wiki';
  if (rel.startsWith('design-studio')) return 'design';
  if (rel.startsWith('software-projects')) return 'code';
  if (rel.startsWith('game-lab')) return 'game';
  return 'global';
}

function getProjectHash(cwd) {
  const { execSync } = require('child_process');
  try {
    const remote = execSync('git remote get-url origin', {
      cwd, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'], timeout: 3000,
    }).trim();
    return crypto.createHash('sha256').update(remote).digest('hex').substring(0, 8);
  } catch {
    return crypto.createHash('sha256').update(path.resolve(cwd)).digest('hex').substring(0, 8);
  }
}

const AGENT_MAP = {
  code:   'mew-coder',
  game:   'mew-gamedev',
  design: 'mew-designer',
  wiki:   'mew-learner',
  global: 'mew-chief',
};

function accumulateActivity(workspaceRoot, filePath, silo) {
  const actFile = path.join(workspaceRoot, '.claude', 'session-activity.json');
  let activity = { files_modified: [], tool_calls: 0 };
  if (fs.existsSync(actFile)) {
    try { activity = JSON.parse(fs.readFileSync(actFile, 'utf8')); } catch {}
  }
  if (filePath && !activity.files_modified.includes(filePath)) {
    activity.files_modified.push(filePath);
  }
  activity.tool_calls = (activity.tool_calls || 0) + 1;
  activity.active_agent = AGENT_MAP[silo] || 'mew-chief';
  activity.last_updated = new Date().toISOString();
  try {
    fs.mkdirSync(path.dirname(actFile), { recursive: true });
    fs.writeFileSync(actFile, JSON.stringify(activity, null, 2), 'utf8');
  } catch {}
}

// Phase 3: instinct extraction from tool response patterns
// For now, we detect re-writes of the same file as a potential correction signal
function checkCorrectionSignal(workspaceRoot, filePath, cwd) {
  if (!filePath) return;
  const signalFile = path.join(workspaceRoot, '.claude', 'correction-signals.json');
  let signals = {};
  if (fs.existsSync(signalFile)) {
    try { signals = JSON.parse(fs.readFileSync(signalFile, 'utf8')); } catch {}
  }

  const now = Date.now();
  const REWRITE_WINDOW_MS = 60000;      // rewrites must be within 60s of each other
  const SIGNAL_TTL_MS = 24 * 3600000;   // drop tracking entries older than 24h
  const MIN_REWRITES = 3;               // 2 writes = normal iteration; 3+ = correction signal
  const MAX_PENDING = 50;               // hard cap on the pending queue

  // Prune stale entries so correction-signals.json doesn't grow unbounded
  for (const key of Object.keys(signals)) {
    if (!signals[key] || (now - signals[key].ts) > SIGNAL_TTL_MS) delete signals[key];
  }

  const prev = signals[filePath];
  const count = prev && (now - prev.ts) < REWRITE_WINDOW_MS ? (prev.count || 1) + 1 : 1;
  signals[filePath] = { ts: now, count };
  try { fs.writeFileSync(signalFile, JSON.stringify(signals), 'utf8'); } catch {}

  if (count < MIN_REWRITES) return;

  const silo = detectSilo(cwd, workspaceRoot);
  const projectHash = getProjectHash(cwd);
  const pendingDir = path.join(MEWVAULT_ROOT, 'instincts', 'pending');
  const topic = path.basename(filePath, path.extname(filePath));
  try {
    fs.mkdirSync(pendingDir, { recursive: true });
    const existing = fs.readdirSync(pendingDir);
    if (existing.length >= MAX_PENDING) return;                 // queue full — stop generating
    const slug = topic.replace(/[^a-zA-Z0-9_-]/g, '');
    if (existing.some(f => f.includes(`-${slug}-`) && f.startsWith(`${silo}-rewrite-`))) return; // dedupe per silo+topic
    const instinct = {
      id: `${silo}-rewrite-${slug}-${projectHash}`,
      silo,
      project_hash: projectHash,
      topic,
      wrong_assumption: `${path.basename(filePath)} was rewritten ${count} times in rapid succession`,
      correct_behavior: `Review ${path.basename(filePath)} before writing — verify before first commit`,
      source: 'rapid-rewrite-signal',
      confidence: 0.6,
      confirmed_sessions: 1,
      created: new Date().toISOString(),
      status: 'pending',
    };
    fs.writeFileSync(
      path.join(pendingDir, `${instinct.id}.json`),
      JSON.stringify(instinct, null, 2),
      'utf8'
    );
  } catch {}
}

// ── Impeccable guard ──────────────────────────────────────────────────────────
// Enforcement for the design-quality rules that used to be advisory-only.
// Runs on every Write/Edit to a UI file, in EVERY silo (frontend work happens
// in software-projects too, where design rules never load).
// Feedback reaches Claude via PostToolUse JSON additionalContext (stdout does not).

const UI_EXTS = new Set(['.css', '.scss', '.html', '.tsx', '.jsx', '.vue', '.svelte', '.astro']);

// Deterministic checks for the absolute bans in mew-design rules.
// npx impeccable detect covers more, but this is zero-dependency and instant.
const BAN_PATTERNS = [
  { re: /border-(left|right)\s*:\s*([2-9]|\d{2,})px/i,
    msg: 'side-stripe accent (border-left/right > 1px) — banned; use background tint or spacing instead' },
  { re: /(-webkit-)?background-clip\s*:\s*text/i,
    msg: 'gradient text via background-clip: text — banned' },
  { re: /backdrop-filter\s*:\s*blur/i,
    msg: 'glassmorphism (backdrop-filter blur) — banned by default' },
  { re: /border-radius\s*:\s*(1[7-9]|[2-9]\d|\d{3,})px/i,
    msg: 'border-radius > 16px on cards/inputs — banned' },
  { re: /\brounded-3xl\b/,
    msg: 'Tailwind rounded-3xl (24px) — exceeds the 16px radius ban' },
];

function impeccableGuard(input, toolName, toolInput, filePath, workspaceRoot) {
  if (!filePath || !['Write', 'Edit', 'MultiEdit'].includes(toolName)) return null;
  if (!UI_EXTS.has(path.extname(filePath).toLowerCase())) return null;

  const notes = [];

  // 1. Once per session: anchor the Impeccable flow at the moment UI work starts,
  //    instead of hoping the first-prompt rules are still in attention.
  const sessionId = (input.session_id || 'nosession').replace(/[^a-zA-Z0-9-]/g, '');
  const flag = path.join(require('os').tmpdir(), `mew-impeccable-${sessionId}.flag`);
  if (!fs.existsSync(flag)) {
    try { fs.writeFileSync(flag, new Date().toISOString()); } catch {}
    const projectDir = path.dirname(filePath);
    let hasProduct = false;
    try {
      let dir = projectDir;
      for (let i = 0; i < 6; i++) {
        if (fs.existsSync(path.join(dir, 'PRODUCT.md'))) { hasProduct = true; break; }
        const parent = path.dirname(dir);
        if (parent === dir) break;
        dir = parent;
      }
    } catch {}
    notes.push(
      'UI work detected — the Impeccable flow applies (all silos, not just design-studio):\n' +
      '1. If not done this session: run `node mewvault/.agents/skills/impeccable/scripts/context.mjs`\n' +
      (hasProduct ? '' : '2. No PRODUCT.md found up-tree — run `/impeccable init` before designing.\n') +
      '3. Iterate with named commands (/impeccable typeset|layout|colorize|polish|bolder|quieter <target>).\n' +
      '4. Before presenting as done, run the pre-ship gauntlet: /impeccable audit, clarify, harden.\n' +
      'Absolute bans are enforced by this hook. Full flow: mewvault/.agents/skills/impeccable/SKILL.md'
    );
  }

  // 2. Ban detection on the content just written
  const content = toolInput.content || toolInput.new_string ||
    (Array.isArray(toolInput.edits) ? toolInput.edits.map(e => e.new_string || '').join('\n') : '');
  if (content) {
    const hits = BAN_PATTERNS.filter(b => b.re.test(content)).map(b => b.msg);
    if (hits.length) {
      notes.push(
        `Impeccable ban violation(s) in ${path.basename(filePath)}:\n` +
        hits.map(h => `- ${h}`).join('\n') +
        '\nFix these now — they are absolute bans from .claude/rules/mew-design/design-rules.md.'
      );
    }
  }

  return notes.length ? notes.join('\n\n') : null;
}

function main() {
  const input = readStdin();
  const cwd = input.cwd || process.cwd();
  const toolName = input.tool_name || '';
  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || toolInput.path || '';

  let workspaceRoot = cwd;
  try {
    workspaceRoot = findWorkspaceRoot(cwd);
    const silo = detectSilo(cwd, workspaceRoot);
    accumulateActivity(workspaceRoot, filePath, silo);
    checkCorrectionSignal(workspaceRoot, filePath, cwd);
  } catch {}

  // Graphify: update knowledge graph after source file changes (non-blocking)
  if (filePath) {
    try { runGraphifyUpdate(filePath, cwd); } catch {}
  }

  // Impeccable guard — additionalContext is the only PostToolUse channel Claude sees
  try {
    const guardMsg = impeccableGuard(input, toolName, toolInput, filePath, workspaceRoot);
    if (guardMsg) {
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PostToolUse',
          additionalContext: guardMsg.substring(0, 9000),
        },
      }) + '\n');
    }
  } catch {}

  process.exit(0);
}

main();
