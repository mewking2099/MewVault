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
  } catch (err) {
    logError(err.message);
  }
}

main();
