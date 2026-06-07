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
  const prev = signals[filePath];
  // If same file written twice within 60 seconds, flag as potential correction
  if (prev && (now - prev.ts) < 60000) {
    const silo = detectSilo(cwd, workspaceRoot);
    const projectHash = getProjectHash(cwd);
    const pendingDir = path.join(MEWVAULT_ROOT, 'instincts', 'pending');
    try {
      fs.mkdirSync(pendingDir, { recursive: true });
      const instinct = {
        id: `${silo}-rewrite-${projectHash}-${Date.now()}`,
        silo,
        project_hash: projectHash,
        topic: path.basename(filePath, path.extname(filePath)),
        wrong_assumption: `First version of ${path.basename(filePath)} was immediately revised`,
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

  signals[filePath] = { ts: now };
  try { fs.writeFileSync(signalFile, JSON.stringify(signals), 'utf8'); } catch {}
}

function main() {
  const input = readStdin();
  const cwd = input.cwd || process.cwd();
  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || toolInput.path || '';

  try {
    const workspaceRoot = findWorkspaceRoot(cwd);
    const silo = detectSilo(cwd, workspaceRoot);
    accumulateActivity(workspaceRoot, filePath, silo);
    checkCorrectionSignal(workspaceRoot, filePath, cwd);
  } catch {}

  // Graphify: update knowledge graph after source file changes (non-blocking)
  if (filePath) {
    try { runGraphifyUpdate(filePath, cwd); } catch {}
  }

  process.exit(0);
}

main();
