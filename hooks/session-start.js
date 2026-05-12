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

const AGENT_MAP = {
  code:   { name: 'mew-coder',    model: 'claude-sonnet-4-6', role: 'Implementation, refactoring, test generation' },
  game:   { name: 'mew-gamedev',  model: 'claude-sonnet-4-6', role: 'GDScript, game mechanics, Godot patterns' },
  design: { name: 'mew-designer', model: 'claude-sonnet-4-6', role: 'UX, Figma review, component specs' },
  wiki:   { name: 'mew-learner',  model: 'claude-sonnet-4-6', role: 'Concept distillation, research ingest' },
};
const DEFAULT_AGENT = { name: 'mew-chief', model: 'claude-sonnet-4-6', role: 'Cross-silo orchestration, triage, routing' };

function getAgent(silo) {
  return AGENT_MAP[silo] || DEFAULT_AGENT;
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

function loadActiveMcps(workspaceRoot) {
  try {
    const settingsFile = path.join(workspaceRoot, '.claude', 'settings.json');
    if (!fs.existsSync(settingsFile)) return {};
    const s = JSON.parse(fs.readFileSync(settingsFile, 'utf8'));
    return s.mcpServers || {};
  } catch { return {}; }
}

function queryChromaDb(collection, queryText) {
  const http = require('http');
  return new Promise((resolve) => {
    const body = JSON.stringify({ query_texts: [queryText], n_results: 5 });
    const req = http.request({
      hostname: 'localhost', port: 8000,
      path: `/api/v1/collections/${collection}/query`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const r = JSON.parse(data);
          const docs = (r.documents || [[]])[0] || [];
          resolve(docs.slice(0, 5).map(d => d.substring(0, 200)).join('\n'));
        } catch { resolve(null); }
      });
    });
    req.on('error', () => resolve(null));
    req.setTimeout(2000, () => { req.destroy(); resolve(null); });
    req.write(body);
    req.end();
  });
}

function loadPendingVectorIndex(workspaceRoot) {
  const f = path.join(workspaceRoot, '.claude', 'pending-vector-index.json');
  if (!fs.existsSync(f)) return null;
  try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch { return null; }
}

function getGitRemote(dir) {
  const { spawnSync } = require('child_process');
  const r = spawnSync('git', ['-C', dir, 'remote', 'get-url', 'origin'], { encoding: 'utf8' });
  if (r.status !== 0) return null;
  const url = r.stdout.trim();
  const m = url.match(/github\.com[:/]([^/]+\/[^/.]+)/);
  return m ? m[1] : null;
}

function queryGithubApi(repo, labels, token) {
  const https = require('https');
  const labelParam = labels.map(encodeURIComponent).join(',');
  return new Promise((resolve) => {
    const opts = {
      hostname: 'api.github.com',
      path: `/repos/${repo}/issues?state=open&labels=${labelParam}&per_page=5`,
      headers: { 'User-Agent': 'mewvault-hook', 'Authorization': `Bearer ${token}` },
    };
    const req = https.get(opts, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const issues = JSON.parse(data);
          if (!Array.isArray(issues)) { resolve(null); return; }
          resolve(issues.map(i => {
            const lbls = (i.labels || []).map(l => l.name).join(', ');
            return `- #${i.number} ${i.title}${lbls ? ` [${lbls}]` : ''}`;
          }).join('\n'));
        } catch { resolve(null); }
      });
    });
    req.on('error', () => resolve(null));
    req.setTimeout(3000, () => { req.destroy(); resolve(null); });
  });
}

async function loadGithubIssues(silo, workspaceRoot, currentPhase) {
  try {
    if (!process.env.GITHUB_MCP_ENABLED) return null;
    const mcps = loadActiveMcps(workspaceRoot);
    if (!mcps.github) return null;

    const siloMap = { code: 'software-projects', game: 'game-lab', design: 'design-studio', wiki: 'wiki' };
    const siloDir = siloMap[silo] ? require('path').join(workspaceRoot, siloMap[silo]) : workspaceRoot;
    const repo = getGitRemote(siloDir) || getGitRemote(workspaceRoot);
    if (!repo) return null;

    const token = process.env.GITHUB_TOKEN;
    if (!token) {
      const phase = currentPhase ? `, phase-${currentPhase}` : '';
      return `(GitHub MCP active — use github tool to list open issues on ${repo} with labels: blocked${phase})`;
    }

    const labels = ['blocked'];
    if (currentPhase) labels.push(`phase-${currentPhase}`);
    const issues = await queryGithubApi(repo, labels, token);
    return issues || null;
  } catch { return null; }
}

function getMewWikiPath(workspaceRoot) {
  const pointer = path.join(workspaceRoot, 'mewvault', '.mewwiki');
  if (!fs.existsSync(pointer)) return null;
  const p = fs.readFileSync(pointer, 'utf8').trim();
  return (p && fs.existsSync(p)) ? p : null;
}

function loadMewWikiBrief(workspaceRoot) {
  const wikiPath = getMewWikiPath(workspaceRoot);
  if (!wikiPath) return null;

  const parts = [];

  // Active focus + project list from Brain/North Star.md
  const northStar = path.join(wikiPath, 'Brain', 'North Star.md');
  if (fs.existsSync(northStar)) {
    const text = fs.readFileSync(northStar, 'utf8');
    const focusM = text.match(/## Active Focus\n([\s\S]*?)(?=\n##|$)/);
    const focus = focusM ? focusM[1].replace(/<!--[\s\S]*?-->/g, '').trim() : '';
    if (focus) parts.push(`Focus: ${focus.substring(0, 200)}`);

    const projM = text.match(/## Active Projects\n([\s\S]*?)(?=\n##|$)/);
    const proj = projM ? projM[1].replace(/<!--[\s\S]*?-->/g, '').trim() : '';
    if (proj) parts.push(`Projects:\n${proj.substring(0, 400)}`);
  }

  // _inbox/ count
  const inboxDir = path.join(wikiPath, '_inbox');
  if (fs.existsSync(inboxDir)) {
    try {
      const count = fs.readdirSync(inboxDir).filter(f => f.endsWith('.md')).length;
      if (count > 0) parts.push(`Inbox: ${count} item(s) pending review (mewwiki/_inbox/)`);
    } catch {}
  }

  // Stale projects: last_session > 14 days
  const projDir = path.join(wikiPath, 'Projects');
  if (fs.existsSync(projDir)) {
    const stale = [];
    const cutoff = Date.now() - 14 * 86400000;
    try {
      for (const slug of fs.readdirSync(projDir)) {
        if (slug === '_archive') continue;
        const idx = path.join(projDir, slug, 'index.md');
        if (!fs.existsSync(idx)) continue;
        const m = fs.readFileSync(idx, 'utf8').match(/^last_session:\s*(\S+)/m);
        if (!m) continue;
        const t = new Date(m[1]).getTime();
        if (!isNaN(t) && t < cutoff) {
          stale.push(`${slug} (idle ${Math.floor((Date.now() - t) / 86400000)}d)`);
        }
      }
    } catch {}
    if (stale.length) parts.push(`Stale (>14d idle): ${stale.join(', ')}`);
  }

  return parts.length ? parts.join('\n') : null;
}

async function loadSemanticContext(silo, workspaceRoot) {
  try {
    const mcps = loadActiveMcps(workspaceRoot);
    if (['code', 'game'].includes(silo) && mcps.chromadb) {
      const mewvaultConfPath = path.join(MEWVAULT_ROOT, 'mcp-configs', 'chromadb.json');
      let collection = silo === 'code' ? 'mewvault-code' : 'mewvault-game';
      try {
        const conf = JSON.parse(fs.readFileSync(mewvaultConfPath, 'utf8'));
        collection = (conf.collections || {})[silo] || collection;
      } catch {}
      const result = await queryChromaDb(collection, `${silo} recent session context`);
      if (result) return result;
    }
    // For wiki/doobidoo: stdio-only, surface pending index as reminder
    if (silo === 'wiki' && mcps.doobidoo) {
      const pending = loadPendingVectorIndex(workspaceRoot);
      if (pending && pending.silo === 'wiki') {
        return `(doobidoo index pending from last session — ${pending.timestamp})`;
      }
    }
  } catch {}
  return null;
}

async function main() {
  // CACHE-OPTIMIZATION: Sections 1-2 must come before any dynamic content.
  // Anthropic caches static prompt prefixes; reordering breaks cache hits.
  const input = readStdin();
  const cwd = input.cwd || process.cwd();
  const workspaceRoot = findWorkspaceRoot(cwd);
  const silo = detectSilo(cwd, workspaceRoot);

  const sections = [];
  const agent = getAgent(silo);

  // 1+2: Static rules (cache-eligible — always first)
  const rules = loadRules(workspaceRoot, silo);
  if (rules) sections.push('## Vault Rules\n\n' + rules);

  // 3: Active agent persona
  sections.push(
    `## Active Agent: ${agent.name} (${agent.model})\n\n` +
    `Silo: ${silo || 'global'} | Role: ${agent.role}`
  );

  // 4: Project status (dynamic, whitelisted)
  const status = loadProjectStatus(cwd, workspaceRoot, silo);
  if (status) sections.push('## Current Project\n\n```yaml\n' + status + '\n```');
  const currentPhaseMatch = status && status.match(/current_phase\s*:\s*(\S+)/);
  const currentPhase = currentPhaseMatch ? currentPhaseMatch[1] : null;

  // 5: Recovery detection
  const unwrapped = findUnwrapped(workspaceRoot);
  if (unwrapped.length) {
    sections.push('## Unwrapped Sessions\n\n' +
      'These projects have no auto-wrap on their last log entry. Address before new work:\n' +
      unwrapped.map(p => `- ${p}`).join('\n'));
  }

  // 6: Promoted instincts
  const instincts = loadInstincts(silo);
  if (instincts.length) {
    sections.push('## Active Vault Instincts\n\n' +
      instincts.map(i => `- [${i.silo || 'global'}] ${i.correct_behavior} (${i.confidence})`).join('\n'));
  }

  // 7: Semantic context from vector stores (Phase 4 — graceful degradation)
  const semantic = await loadSemanticContext(silo, workspaceRoot);
  if (semantic) sections.push('## Relevant Context (semantic)\n\n' + semantic);

  // 8: Open GitHub issues (Phase 6 — only when GITHUB_MCP_ENABLED=1 and github MCP configured)
  const githubIssues = await loadGithubIssues(silo, workspaceRoot, currentPhase);
  if (githubIssues) sections.push('## Open GitHub Issues (blocking current phase)\n\n' + githubIssues);

  // 9: MewWiki Brain brief (focus, inbox count, stale alerts)
  const wikibrief = loadMewWikiBrief(workspaceRoot);
  if (wikibrief) sections.push('## MewWiki\n\n' + wikibrief);

  let brief = sections.join('\n\n---\n\n');
  if (brief.length > MAX_CHARS) {
    brief = brief.substring(0, MAX_CHARS) + '\n\n[... truncated to token budget]';
  }

  if (brief.trim()) process.stdout.write(brief + '\n');
}

main();
