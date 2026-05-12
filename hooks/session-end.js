#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const MEWVAULT_ROOT = process.env.MEWVAULT_ROOT || path.join(__dirname, '..');
const ERROR_LOG = path.join(os.homedir(), '.mewvault-hook-errors.log');

function logError(msg) {
  try { fs.appendFileSync(ERROR_LOG, `[${new Date().toISOString()}] session-end: ${msg}\n`); } catch {}
}

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

function findActiveProject(cwd, workspaceRoot) {
  let dir = path.resolve(cwd);
  while (dir.length >= workspaceRoot.length) {
    if (fs.existsSync(path.join(dir, 'Project_Status.md'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function ts() {
  return new Date().toISOString().replace('T', ' ').substring(0, 16);
}

function prependToLog(logFile, entry) {
  if (!fs.existsSync(logFile)) return;
  const content = fs.readFileSync(logFile, 'utf8');
  const marker = '## Entries\n';
  const idx = content.indexOf(marker);
  let updated;
  if (idx !== -1) {
    const insertAt = idx + marker.length;
    updated = content.substring(0, insertAt) + '\n' + entry + '\n' + content.substring(insertAt);
  } else {
    updated = content + '\n' + entry + '\n';
  }
  fs.writeFileSync(logFile, updated, 'utf8');
}

function readAndClearActivity(workspaceRoot) {
  const f = path.join(workspaceRoot, '.claude', 'session-activity.json');
  if (!fs.existsSync(f)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(f, 'utf8'));
    fs.unlinkSync(f);
    return data;
  } catch { return null; }
}

function detectSilo(cwd, workspaceRoot) {
  const rel = path.relative(workspaceRoot, path.resolve(cwd)).replace(/\\/g, '/');
  if (rel.startsWith('wiki')) return 'wiki';
  if (rel.startsWith('design-studio')) return 'design';
  if (rel.startsWith('software-projects')) return 'code';
  if (rel.startsWith('game-lab')) return 'game';
  return null;
}

function loadActiveMcps(workspaceRoot) {
  try {
    const f = path.join(workspaceRoot, '.claude', 'settings.json');
    if (!fs.existsSync(f)) return {};
    return JSON.parse(fs.readFileSync(f, 'utf8')).mcpServers || {};
  } catch { return {}; }
}

function getMewWikiPath(workspaceRoot) {
  const pointer = path.join(workspaceRoot, 'mewvault', '.mewwiki');
  if (!fs.existsSync(pointer)) return null;
  const p = fs.readFileSync(pointer, 'utf8').trim();
  return (p && fs.existsSync(p)) ? p : null;
}

function runWikiSync(workspaceRoot) {
  const wikiPath = getMewWikiPath(workspaceRoot);
  if (!wikiPath) return;
  const mewPy = path.join(workspaceRoot, 'mewvault', 'mew.py');
  if (!fs.existsSync(mewPy)) return;
  try {
    const { spawnSync } = require('child_process');
    spawnSync('python', [mewPy, 'wiki', 'sync'], {
      cwd: path.join(workspaceRoot, 'mewvault'),
      timeout: 20000,
      stdio: 'pipe',
    });
  } catch {}
}

function writeMemorySummary(wikiPath, projectSlug, summary, fileCount) {
  if (fileCount < 3) return;
  const memoriesPath = path.join(wikiPath, 'Brain', 'Memories.md');
  if (!fs.existsSync(memoriesPath)) return;
  const date = new Date().toISOString().split('T')[0];
  const entry = `\n- **${date}** · ${projectSlug}: ${summary} (${fileCount} files)`;
  try { fs.appendFileSync(memoriesPath, entry, 'utf8'); } catch {}
}

function writePendingVectorIndex(workspaceRoot, silo, summary, filesModified) {
  try {
    const f = path.join(workspaceRoot, '.claude', 'pending-vector-index.json');
    fs.writeFileSync(f, JSON.stringify({
      silo,
      summary,
      files_modified: filesModified || [],
      timestamp: new Date().toISOString(),
    }), 'utf8');
  } catch {}
}

function indexToChromaDb(collection, docId, text) {
  const http = require('http');
  const body = JSON.stringify({
    ids: [docId],
    documents: [text],
    metadatas: [{ source: 'session-end', timestamp: new Date().toISOString() }],
  });
  const req = http.request({
    hostname: 'localhost', port: 8000,
    path: `/api/v1/collections/${collection}/upsert`,
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
  }, () => {});
  req.on('error', () => {});
  req.setTimeout(3000, () => req.destroy());
  req.write(body);
  req.end();
}

function main() {
  const input = readStdin();
  const cwd = input.cwd || process.cwd();

  try {
    const workspaceRoot = findWorkspaceRoot(cwd);
    const projectDir = findActiveProject(cwd, workspaceRoot);
    if (!projectDir) return;

    const activity = readAndClearActivity(workspaceRoot);
    let summary = 'session ended';
    if (activity && activity.files_modified && activity.files_modified.length > 0) {
      const names = activity.files_modified.slice(0, 3).map(f => path.basename(f));
      const extra = activity.files_modified.length > 3 ? ` +${activity.files_modified.length - 3} more` : '';
      summary = `modified ${names.join(', ')}${extra}`;
    }

    const logFile = path.join(projectDir, 'log.md');
    const entry = `- **${ts()}** — auto-wrap: ${summary} [auto-wrap]`;
    prependToLog(logFile, entry);

    // Suggested commit message
    const claudeDir = path.join(workspaceRoot, '.claude');
    if (fs.existsSync(claudeDir)) {
      const msg = `chore: session wrap ${ts().split(' ')[0]}\n\n- ${summary}`;
      fs.writeFileSync(path.join(claudeDir, 'last-session-message.txt'), msg, 'utf8');
    }

    // MewWiki: auto-sync on session end + write Memories entry if substantial
    try {
      const filesModified = (activity && activity.files_modified) ? activity.files_modified : [];
      runWikiSync(workspaceRoot);
      const wikiPath = getMewWikiPath(workspaceRoot);
      if (wikiPath) writeMemorySummary(wikiPath, path.basename(projectDir), summary, filesModified.length);
    } catch {}

    // Phase 4: vector store indexing (fire-and-forget, never throws)
    try {
      const silo = detectSilo(cwd, workspaceRoot);
      const mcps = loadActiveMcps(workspaceRoot);
      const filesModified = (activity && activity.files_modified) ? activity.files_modified : [];
      if (['code', 'game'].includes(silo) && mcps.chromadb) {
        const collection = silo === 'code' ? 'mewvault-code' : 'mewvault-game';
        const docId = `session-${ts().replace(/[: ]/g, '-')}`;
        const text = [summary, ...filesModified.map(f => path.basename(f))].join(' | ');
        indexToChromaDb(collection, docId, text);
      } else if (silo === 'wiki' && mcps.doobidoo) {
        // doobidoo is stdio-only — stage for next session-start to surface
        writePendingVectorIndex(workspaceRoot, silo, summary, filesModified);
      }
    } catch {}
  } catch (err) {
    logError(err.message);
  }
}

main();
