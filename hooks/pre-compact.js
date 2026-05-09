#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

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
  return 'workspace';
}

function main() {
  const input = readStdin();
  const cwd = input.cwd || process.cwd();

  try {
    const workspaceRoot = findWorkspaceRoot(cwd);
    const silo = detectSilo(cwd, workspaceRoot);
    const snapshotsDir = path.join(workspaceRoot, '.claude', 'context-snapshots');
    fs.mkdirSync(snapshotsDir, { recursive: true });

    const mewPy = path.join(MEWVAULT_ROOT, 'mew.py');
    const date = new Date().toISOString().split('T')[0];
    const snapshotFile = path.join(snapshotsDir, `${silo}-${date}.md`);

    // Run mew compact --semantic
    const result = spawnSync(
      process.platform === 'win32' ? 'python' : 'python3',
      [mewPy, 'compact', '--semantic', '--budget', '4000'],
      { cwd: workspaceRoot, encoding: 'utf8', timeout: 15000 }
    );

    const output = (result.stdout || '').trim();
    if (output) {
      fs.writeFileSync(
        snapshotFile,
        `# Context Snapshot — ${silo} — ${date}\n\n${output}\n`,
        'utf8'
      );

      // Keep only 5 most recent snapshots
      const all = fs.readdirSync(snapshotsDir)
        .filter(f => f.endsWith('.md'))
        .map(f => ({ f, mt: fs.statSync(path.join(snapshotsDir, f)).mtimeMs }))
        .sort((a, b) => b.mt - a.mt);
      for (const { f } of all.slice(5)) {
        try { fs.unlinkSync(path.join(snapshotsDir, f)); } catch {}
      }
    }
  } catch {}

  // PreCompact must write summary to stdout (survives compaction as preserved context)
  const cwd2 = input.cwd || process.cwd();
  const snapshotsDir = path.join(findWorkspaceRoot(cwd2), '.claude', 'context-snapshots');
  const files = fs.existsSync(snapshotsDir) ? fs.readdirSync(snapshotsDir).filter(f => f.endsWith('.md')) : [];
  if (files.length) {
    const latest = files.sort().pop();
    try {
      const snap = fs.readFileSync(path.join(snapshotsDir, latest), 'utf8');
      process.stdout.write(snap);
    } catch {}
  }
}

main();
