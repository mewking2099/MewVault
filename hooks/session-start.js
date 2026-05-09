#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');

const MEWVAULT_ROOT = process.env.MEWVAULT_ROOT || path.join(__dirname, '..');
const MAX_TOKENS = parseInt(process.env.MEW_SESSION_START_MAX_TOKENS || '6000', 10);
const MAX_CHARS = MAX_TOKENS * 4;

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
  return null;
}

function loadRules(workspaceRoot, silo) {
  const parts = [];
  const load = (dir) => {
    if (!fs.existsSync(dir)) return;
    for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.md')).sort()) {
      try { parts.push(fs.readFileSync(path.join(dir, f), 'utf8').trim()); } catch {}
    }
  };
  load(path.join(workspaceRoot, '.claude', 'rules', 'mew-common'));
  if (silo) load(path.join(workspaceRoot, '.claude', 'rules', `mew-${silo}`));
  return parts.join('\n\n');
}

const WHITELIST = {
  code:   ['current_phase', 'stack', 'open_threads', 'tier', 'plan_approved'],
  design: ['current_phase', 'figma_file_key', 'greenlit', 'tier'],
  game:   ['current_phase', 'concepts_count', 'mechanics_count', 'tier'],
  wiki:   ['inbox_count', 'orphan_concepts'],
};

function loadProjectStatus(cwd, workspaceRoot, silo) {
  let dir = path.resolve(cwd);
  while (dir.startsWith(workspaceRoot)) {
    const f = path.join(dir, 'Project_Status.md');
    if (fs.existsSync(f)) {
      const lines = fs.readFileSync(f, 'utf8').split('\n');
      const allowed = WHITELIST[silo] || [];
      if (allowed.length === 0) return lines.slice(0, 20).join('\n');
      return lines.filter(l => {
        const k = l.split(':')[0].trim().replace(/^-+/, '').trim();
        return l === '---' || allowed.includes(k);
      }).join('\n');
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function findUnwrapped(workspaceRoot) {
  const results = [];
  for (const silo of ['software-projects', 'game-lab', 'design-studio']) {
    const siloPath = path.join(workspaceRoot, silo);
    if (!fs.existsSync(siloPath)) continue;
    try {
      for (const project of fs.readdirSync(siloPath)) {
        const logFile = path.join(siloPath, project, 'log.md');
        if (!fs.existsSync(logFile)) continue;
        const lines = fs.readFileSync(logFile, 'utf8')
          .split('\n').filter(l => /^\s*-\s*\*\*/.test(l));
        if (lines.length && !lines[0].includes('[auto-wrap]')) {
          results.push(`${silo}/${project}`);
        }
      }
    } catch {}
  }
  return results;
}

function loadInstincts(silo) {
  const promotedDir = path.join(MEWVAULT_ROOT, 'instincts', 'promoted');
  if (!fs.existsSync(promotedDir)) return [];
  const instincts = [];
  try {
    for (const f of fs.readdirSync(promotedDir).filter(f => f.endsWith('.json'))) {
      try {
        const d = JSON.parse(fs.readFileSync(path.join(promotedDir, f), 'utf8'));
        if (!silo || d.silo === silo || d.silo === 'global') instincts.push(d);
      } catch {}
    }
  } catch {}
  return instincts.sort((a, b) => (b.confidence || 0) - (a.confidence || 0)).slice(0, 5);
}

function main() {
  const input = readStdin();
  const cwd = input.cwd || process.cwd();
  const workspaceRoot = findWorkspaceRoot(cwd);
  const silo = detectSilo(cwd, workspaceRoot);

  const sections = [];

  // 1+2: Static rules (cache-eligible — always first)
  const rules = loadRules(workspaceRoot, silo);
  if (rules) sections.push('## Vault Rules\n\n' + rules);

  // 3: Project status (dynamic, whitelisted)
  const status = loadProjectStatus(cwd, workspaceRoot, silo);
  if (status) sections.push('## Current Project\n\n```yaml\n' + status + '\n```');

  // 4: Recovery detection
  const unwrapped = findUnwrapped(workspaceRoot);
  if (unwrapped.length) {
    sections.push('## ⚠ Unwrapped Sessions\n\n' +
      'These projects have no auto-wrap on their last log entry. Address before new work:\n' +
      unwrapped.map(p => `- ${p}`).join('\n'));
  }

  // 5: Promoted instincts
  const instincts = loadInstincts(silo);
  if (instincts.length) {
    sections.push('## Active Vault Instincts\n\n' +
      instincts.map(i => `- [${i.silo || 'global'}] ${i.correct_behavior} (${i.confidence})`).join('\n'));
  }

  let brief = sections.join('\n\n---\n\n');
  if (brief.length > MAX_CHARS) {
    brief = brief.substring(0, MAX_CHARS) + '\n\n[... truncated to token budget]';
  }

  if (brief.trim()) process.stdout.write(brief + '\n');
}

main();
