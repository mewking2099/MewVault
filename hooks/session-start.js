#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const MEWVAULT_ROOT = process.env.MEWVAULT_ROOT || path.join(__dirname, '..');
const MAX_TOKENS = parseInt(process.env.MEW_SESSION_START_MAX_TOKENS || '3000', 10);
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
  if (rel.startsWith('idea-hub')) return 'idea';
  if (rel.startsWith('mewvault') || rel === '') return 'mewvault';
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
  code:     { name: 'mew-coder',    model: 'claude-sonnet-5',   role: 'Implementation, refactoring, test generation' },
  game:     { name: 'mew-gamedev',  model: 'claude-sonnet-5',   role: 'GDScript, game mechanics, Godot patterns' },
  design:   { name: 'mew-designer', model: 'claude-sonnet-5',   role: 'UX, Figma review, component specs' },
  wiki:     { name: 'mew-learner',  model: 'claude-sonnet-4-6', role: 'Concept distillation, research ingest' },
  idea:     { name: 'mew-ideator',  model: 'claude-sonnet-5',   role: 'Idea capture, expansion, feasibility routing' },
  mewvault: { name: 'mew-chief',    model: 'claude-sonnet-5',   role: 'CLI engine, hooks, skills, agent array' },
};
const DEFAULT_AGENT = { name: 'mew-chief', model: 'claude-sonnet-5', role: 'Cross-silo orchestration, triage, routing' };

function getAgent(silo) {
  return AGENT_MAP[silo] || DEFAULT_AGENT;
}

const WHITELIST = {
  code:   ['current_phase', 'stack', 'open_threads', 'tier', 'plan_approved'],
  design: ['current_phase', 'figma_file_key', 'greenlit', 'tier', 'last_audit', 'audit_scores', 'open_p0'],
  game:   ['current_phase', 'concepts_count', 'mechanics_count', 'tier'],
  wiki:   ['inbox_count', 'orphan_concepts'],
  idea:   ['active_ideas', 'seed_count', 'exploring_count', 'validated_count', 'tier'],
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
  for (const silo of ['software-projects', 'game-lab', 'design-studio', 'idea-hub']) {
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
  if (!fs.existsSync(promotedDir)) return { json: [], md: [] };
  const json = [];
  const md = [];
  try {
    for (const f of fs.readdirSync(promotedDir)) {
      try {
        if (f.endsWith('.json')) {
          const d = JSON.parse(fs.readFileSync(path.join(promotedDir, f), 'utf8'));
          if (!silo || d.silo === silo || d.silo === 'global') json.push(d);
        } else if (f.endsWith('.md')) {
          md.push({ name: f.replace(/\.md$/, ''), content: fs.readFileSync(path.join(promotedDir, f), 'utf8') });
        }
      } catch {}
    }
  } catch {}
  return { json: json.sort((a, b) => (b.confidence || 0) - (a.confidence || 0)).slice(0, 5), md };
}

function loadAgentDispatcher(workspaceRoot) {
  try {
    const agentsDir = path.join(workspaceRoot, 'mewvault', 'agents');
    const indexPath = path.join(agentsDir, '.routing-index.json');
    const dispatcherPath = path.join(agentsDir, 'mew-chief', 'skills', 'dispatcher.md');

    if (!fs.existsSync(dispatcherPath)) return null;

    // Load dispatcher skill (strip frontmatter)
    let dispatcher = fs.readFileSync(dispatcherPath, 'utf8');
    if (dispatcher.startsWith('---')) {
      const end = dispatcher.indexOf('---', 3);
      if (end !== -1) dispatcher = dispatcher.slice(end + 3).trimStart();
    }

    // Build compact routing index string
    let indexBlock = '_(run `mew agent sync` to build the routing index)_';
    if (fs.existsSync(indexPath)) {
      const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
      const lines = [];
      for (const [agent, skills] of Object.entries(index)) {
        if (!skills.length) continue;
        const triggerSummary = skills
          .flatMap(s => s.triggers || [])
          .slice(0, 6)
          .join(', ');
        lines.push(`- **${agent}**: ${triggerSummary || '(no triggers)'}`);
        for (const skill of skills) {
          lines.push(`  - skill: ${skill.name}${skill.description ? ' — ' + skill.description : ''}`);
        }
      }
      indexBlock = lines.join('\n');
    }

    return dispatcher.replace('{{ROUTING_INDEX}}', indexBlock);
  } catch { return null; }
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

function loadPriorSession(cwd, workspaceRoot) {
  try {
    // Match by nearest ancestor project name
    let dir = path.resolve(cwd);
    while (dir.startsWith(workspaceRoot)) {
      if (fs.existsSync(path.join(dir, 'Project_Status.md'))) {
        const projectName = path.basename(dir);
        const tmpFile = path.join(os.homedir(), '.claude', 'sessions', `${projectName}-session.tmp`);
        if (!fs.existsSync(tmpFile)) return null;
        let content = fs.readFileSync(tmpFile, 'utf8');
        const MAX = 8000;
        if (content.length > MAX) content = content.substring(0, MAX) + '\n[... truncated]';
        return content;
      }
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  } catch {}
  return null;
}

function checkServiceHealth(host, port, path) {
  const http = require('http');
  return new Promise((resolve) => {
    const req = http.request(
      { hostname: host, port, path, method: 'GET' },
      (res) => { resolve(res.statusCode < 500); }
    );
    req.on('error', () => resolve(false));
    req.setTimeout(1500, () => { req.destroy(); resolve(false); });
    req.end();
  });
}

async function checkServices(workspaceRoot) {
  const checks = [
    {
      name: 'Headroom',
      port: 8787,
      path: '/health',
      hint: 'bash proxy/start-headroom.sh',
      detail: 'Context compression unavailable · launch with ANTHROPIC_BASE_URL=http://localhost:8787',
    },
    {
      name: 'LiteLLM proxy',
      port: 4000,
      path: '/health',
      hint: 'bash proxy/start-proxy.sh',
      detail: 'DeepSeek dispatch unavailable',
    },
  ];

  const mcps = loadActiveMcps(workspaceRoot);
  checks.push({
    name: 'ChromaDB',
    port: 8001,
    path: '/api/v2/heartbeat',
    hint: 'bash proxy/install-chromadb-daemon.sh',
    detail: 'Semantic context unavailable',
  });

  const results = await Promise.all(
    checks.map(async (c) => ({ ...c, up: await checkServiceHealth('localhost', c.port, c.path) }))
  );

  return results;
}

function getMcpToolCount(workspaceRoot) {
  try {
    const s = JSON.parse(fs.readFileSync(path.join(workspaceRoot, '.claude', 'settings.json'), 'utf8'));
    return Object.keys(s.mcpServers || {}).length;
  } catch { return 0; }
}

function getModelHint(status) {
  if (!status) return null;
  const m = status.match(/tier\s*:\s*(\S+)/i);
  const tier = m ? m[1].toLowerCase() : null;
  if (tier === 'mewking') return 'Model hint: Opus for architecture decisions · Sonnet for implementation · Haiku for search/exploration';
  if (tier === 'stalk') return 'Model hint: Sonnet for implementation · Opus for architecture calls';
  if (tier === 'pounce') return 'Model hint: Haiku for exploration · Sonnet for implementation';
  return null;
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

function loadMemoryRecall(silo, workspaceRoot) {
  try {
    const { spawnSync } = require('child_process');
    const mewPy = path.join(workspaceRoot, 'mewvault', 'mew.py');
    if (!fs.existsSync(mewPy)) return null;
    const spawnArgs = [mewPy, 'memory', 'recall', '--limit', '5'];
    if (silo) spawnArgs.push('--silo', silo);
    const r = spawnSync('python', spawnArgs, {
      cwd: workspaceRoot,
      encoding: 'utf8',
      timeout: 3000,
    });
    const out = r.stdout && r.stdout.trim();
    if (!out || r.status !== 0 || out.startsWith('No entries') || out.startsWith('Error')) return null;
    return out;
  } catch { return null; }
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
    // doobidoo is stdio-only (an MCP tool Claude calls, not queryable from this
    // hook) — so close the retrieval loop by instructing Claude to consult it.
    if (mcps.doobidoo) {
      const pending = loadPendingVectorIndex(workspaceRoot);
      const pendingNote = (pending && pending.silo === silo)
        ? ` (index pending from last session — ${pending.timestamp})` : '';
      return 'Semantic memory (doobidoo) is active and indexes mewwiki — past decisions, ' +
        'gotchas, and concept pages. Before starting substantive work on a project, call ' +
        '`mcp__doobidoo__retrieve_memory` with 2-3 keywords from the task to surface ' +
        'relevant prior decisions. Cite anything you use as (source: mewwiki).' + pendingNote;
    }
  } catch {}
  return null;
}

// ---------------------------------------------------------------------------
// Conversational triggers — plain English replaces slash commands
// ---------------------------------------------------------------------------

const TRIGGERS = [
  // ── CLI command routing — plain English → mew commands (added 2026-07-08) ──
  // Each runs the command via Bash and presents results conversationally.
  {
    pattern: /^(health check|vault health|is everything (ok|okay|working)|run doctor|doctor)\b/i,
    name: 'doctor',
    instructions: `## Command: mew doctor

Run \`python3 mewvault/mew.py doctor\` via Bash from the workspace root. Present the results conversationally: all-ok gets one line; for each warn/fail explain what it means and give the exact fix. Offer to apply fixes that are file edits.`,
  },
  {
    pattern: /^(dashboard|show (me )?(the )?dashboard|open (the )?dashboard|vault overview)\b/i,
    name: 'dashboard',
    instructions: `## Command: mew dashboard

Run \`python3 mewvault/mew.py dashboard\` via Bash from the workspace root (opens in browser automatically). Then summarize in 2-3 lines: project count, anything stale, doctor status, open audit P0s.`,
  },
  {
    pattern: /^(agent status|did (the )?agents? (run|work)|agent activity|show agents)\b/i,
    name: 'agent-status',
    instructions: `## Command: mew agent status

Run \`python3 mewvault/mew.py agent status\` via Bash. Report: dispatches this week, any blocked dispatches (missing model param — explain that means the model table was ignored), and whether the ledger looks healthy. An empty ledger after sessions with expected agent work means dispatch is broken; say so plainly.`,
  },
  {
    pattern: /^(token (usage|report|burn)|usage report|how (many|much) tokens|burn rate|cache hit)\b/i,
    name: 'usage-report',
    instructions: `## Command: mew usage --report

Run \`python3 mewvault/mew.py usage --report\` via Bash. Highlight the cache-hit ratio: above 80% is healthy; below 50% means prompt-prefix invalidation (see wiki/headroom-postmortem.md) — flag it and investigate.`,
  },
  {
    pattern: /^(install ci|set ?up ci|add ci)\b/i,
    name: 'ci-install',
    instructions: `## Command: mew ci install

Run \`python3 mewvault/mew.py ci install\` via Bash. Then remind the user: each project needs a commit+push for the workflow to activate, and results are read as green/red checks on GitHub — no code reading required.`,
  },
  {
    pattern: /^(token drift|check (design |figma )?tokens|tokens? diff)\b/i,
    name: 'token-drift',
    instructions: `## Command: mew design tokens --diff

Determine the design project (from cwd, or ask). Run \`python3 mewvault/mew.py design tokens --diff --project <name>\` via Bash. If it asks for a Figma variables snapshot, fetch \`get_variable_defs\` via the Figma MCP yourself, save the JSON to <project>/assets/figma-variables.json, and re-run. Present drift as matched / value drift / missing, with suggested fixes.`,
  },
  {
    pattern: /^(prepare handoff( for)?|handoff package( for)?)\s+(.+)/i,
    name: 'design-handoff',
    args: (p) => p.replace(/^(prepare handoff( for)?|handoff package( for)?)\s+/i, '').trim(),
    instructions: (project) => `## Command: mew package --design

Run \`python3 mewvault/mew.py package ${project || '<project>'} --design\` via Bash. Report what was assembled and what's missing (e.g. no PRODUCT.md, no audit scores — suggest running the design-session gauntlet first). Never push to Drive without explicit confirmation.`,
  },
  {
    pattern: /^(sync (the )?wiki|wiki sync)\b/i,
    name: 'wiki-sync',
    instructions: `## Command: mew wiki sync

Run \`python3 mewvault/mew.py wiki sync\` via Bash from the workspace root. Report projects synced, inbox count, and whether the semantic re-index kicked off.`,
  },
  {
    pattern: /^spec\s+(.+)/i,
    name: 'spec',
    args: (p) => p.replace(/^spec\s+/i, '').trim(),
    instructions: (feature) => `## Workflow: Spec — ${feature || '<feature>'}

Spec-driven development. No implementation happens in this workflow — only the spec.

**1. Source** — find the brief: check \`raw/\` for a matching document; if none, interview the user (problem, who it's for, what "working" looks like).

**2. Draft** — write \`specs/${(feature || 'feature').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.md\` from \`mewvault/templates/spec.md.tmpl\`. The acceptance criteria are the contract: numbered AC-n, Given/When/Then, each one independently testable. Include edge cases (empty, long input, errors, offline) and an explicit out-of-scope list.

**3. Review gate** — present the spec and STOP. The user reviews acceptance criteria in product language. Do not write any code, tests included, until they approve. On approval set \`status: approved\` in the spec.

**4. Hand-off note** — after approval, update Project_Status.md next_action to "implement specs/<feature>.md — tests first, from AC-1..AC-n". The TDD gate enforces tests-before-code on stalk/mewking projects.

This is the workflow that lets a non-coding product lead control quality: you approve the criteria, the tests enforce them, CI verifies them.`,
  },
  {
    pattern: /^critique\s+(.+)/i,
    name: 'critique',
    args: (p) => p.replace(/^critique\s+/i, '').trim(),
    instructions: (target) => `## Workflow: Critique — ${target || '<target>'}

Structured design critique from pixels. Works on Figma frames, local builds, and competitor pages.

**1. Capture** — get a screenshot of the target:
- Figma URL → Figma MCP \`get_screenshot\`
- Local/live URL → Claude-in-Chrome navigate + screenshot, or ask the user to paste one
- Pasted image → use directly

**2. Context** — read the project's PRODUCT.md (audience, voice, lane, anti-references) if this is our project. Competitor targets get critiqued against OUR product's positioning.

**3. Critique** — assess against: visual hierarchy (can the eye find the primary action in 3s?), typography (scale, rhythm, pairing), color and contrast (a11y + intent), density and spacing for the lane, copy tone vs PRODUCT.md voice, states visible (empty/error/loading implied?), and the Impeccable anti-patterns list.

**4. Findings** — severity-ranked (P0 blocks shipping → P3 nitpick), each with: what, where, why it matters, concrete fix. End with the two strongest things — critique that only finds faults is half a critique.

**5. File it** — offer to write \`wiki/critique-<slug>-<date>.md\` in the current design project (flows to mewwiki on sync). For competitor critiques, offer \`mewwiki/Knowledge/competitors/<name>-<date>.md\` instead.`,
  },
  {
    pattern: /^(design session|start design|ui session|design work on)\b/i,
    name: 'design-session',
    instructions: `## Workflow: Design Session

Act as mew-designer. Set up the Impeccable loop before touching any file.

**1. Context** — run \`node mewvault/.agents/skills/impeccable/scripts/context.mjs\` (once per session).

**2. Product context** — check the project root for PRODUCT.md and DESIGN.md. Missing PRODUCT.md → run \`/impeccable init\` (short interview: audience, lane, voice, anti-references) before anything else.

**3. Lane** — state whether this is **brand** work (landing/campaign/editorial: distinctive type, committed palette) or **product** work (app UI/dashboard: density, semantic states, components). Confirm with the user if ambiguous.

**4. Figma** — if the project's Project_Status.md has a figma_file_key, offer to pull current frames via the Figma MCP before proposing changes. Never transcribe measurements manually.

**5. Iterate** — use named Impeccable commands (/impeccable typeset|layout|colorize|polish|bolder|quieter <target>), not ad-hoc CSS edits.

**6. Before calling anything done** — pre-ship gauntlet: /impeccable audit → clarify → harden. Report the audit scores to the user, then persist them in Project_Status.md:
\`last_audit: <YYYY-MM-DD>\`, \`audit_scores: a11y=<n> perf=<n> theming=<n> responsive=<n> antipatterns=<n>\`, \`open_p0: <count>\`.
The phase gate blocks moving to handoff/delivery while open_p0 > 0.

Absolute bans are hook-enforced on every UI file write. Design decisions go to wiki/ as concept pages linking the Figma frame that informed them.`,
  },
  {
    pattern: /^(weekly review|week(ly)? wrap|review the week)\b/i,
    name: 'weekly-review',
    instructions: `## Workflow: Weekly Review

Act as mew-archivist (dispatch with model haiku if using the Agent tool). Digest the week.

**1. Gather** — read the last 7 days of \`log.md\` entries across all silo projects, plus \`.claude/agent-dispatches.jsonl\` (agent activity) and \`.claude/doctor-status.json\` (health).

**2. Digest** — write a weekly note to \`mewwiki/Brain/Memories/<YYYY>-W<week>.md\` with: what shipped, decisions made (link Operations/Decisions pages), what stalled and why, agent/model usage summary, one lesson worth keeping.

**3. Stale nudges** — list projects with no log entry in 14+ days; for each, ask: continue, archive, or abandon? Do not act without an answer.

**4. Inbox** — count \`mewwiki/_inbox/\`; if items are older than 7 days, propose routing for each (wait for confirmation).

**5. Sync** — run \`mew wiki sync\` so the weekly note reaches Obsidian, then suggest a commit message.

Keep the note under 40 lines. Facts with sources, no filler.`,
  },
  {
    pattern: /^(standup|stand[\s-]?up|morning brief|good morning)\b/i,
    name: 'standup',
    instructions: `## Workflow: Standup

Morning brief. Run these steps in parallel, then format the output.

**1. North Star** — read \`mewwiki/Brain/North Star.md\` (path from \`mewvault/.mewwiki\`). Extract active focus and project list.

**2. Active projects** — read \`Project_Status.md\` for each active project across silos (software-projects/, design-studio/, game-lab/). For each: slug, status, current_phase, next_action, blockers.

**3. Inbox** — count files in \`mewwiki/_inbox/\`. List names if ≤5, else just count.

**4. Open PRs** — run \`gh pr list --state open --json number,title,headRefName,isDraft\` for each silo that has a GitHub remote. Skip silos with no remote.

**5. Google Calendar** (skip gracefully if not connected) — if a Google Calendar MCP is available, call it for today's events.

**5b. Figma comments** (skip gracefully if Figma MCP unavailable) — for each active design project whose Project_Status.md has a \`figma_file_key\`, fetch unresolved comments via the Figma MCP. Report per project: \`<project>: <N> unresolved comment(s) (oldest <age>)\`. Omit projects with zero.

Output format:
\`\`\`
## Standup — <date>

### Focus
<north star active focus>

### Active Projects
| Project | Phase | Next action | Blockers |
|---------|-------|-------------|----------|
...

### Today
<calendar events or omit>

### Open PRs
<list or "none">

### Inbox
<count> item(s) in mewwiki/_inbox/ waiting for review.
\`\`\`

Keep it scannable. No prose paragraphs. One terminal screen.`,
  },
  {
    pattern: /^(wrap[\s-]?up|end session|done for (the )?day|finishing up|session end)\b/i,
    name: 'wrap-up',
    instructions: `## Workflow: Wrap Up

End the session cleanly.

**1. Detect active project** — use cwd to determine the silo project. If ambiguous, ask.

**2. Gather summary** — ask: "What happened this session? (one sentence to a few bullet points)"

**2b. Definition of Done (code projects only)** — before writing the log, run the project's checks and capture pass/fail:
\`npm run typecheck --if-present && npm run lint --if-present && npm test --if-present && npm run build --if-present\`
All pass → log entry is normal. Any fail → tag the entry \`[incomplete]\`, set \`next_action\` to the first failure, and tell the user plainly: the session's work is NOT verified. Never claim "done" over a red check. If the session implemented a spec, reference its criteria: "AC-1 ✓ AC-2 ✓ AC-3 deferred".

**3. Write log entry** — append to the project's \`log.md\` under \`## Entries\` (newest on top):
\`- **<today YYYY-MM-DD>** — <summary> [auto-wrap]\`
Update \`Project_Status.md\`: \`last_session\`, \`last_wrap\` = today; \`next_action\` = ask if not obvious.

**3b. Visual snapshots (design/frontend projects only)** — if \`snapshot.routes.json\` exists in the project root and the dev server or build is runnable, run \`node mewvault/scripts/snapshot.mjs <project-root>\` and report changed routes. Skip silently if Playwright is not installed.

**4. Check orphaned notes** — scan \`mewwiki/_inbox/\` for files older than today. List any unrouted items.

**5. Run wiki sync** — \`python mew.py wiki sync\`. Report what synced.

**6. Suggest commit** — based on the summary, suggest a commit message:
\`<type>: <summary in imperative mood>\`
Types: feat, fix, refactor, docs, chore, wip.
Write to \`mewvault/.claude/last-session-message.txt\`.

**7. Print close**:
\`\`\`
Session wrapped.
Log: <project>/log.md ✓
Wiki sync: <N> project(s) updated ✓
Commit suggestion: <message>
\`\`\``,
  },
  {
    pattern: /^dump[\s—–-]/i,
    name: 'dump',
    args: (prompt) => prompt.replace(/^dump[\s—–-]+/i, '').trim(),
    instructions: (args) => `## Workflow: Dump

Content to route: "${args || '(see user message)'}"

**1. Classify** — determine content type:

| Type | Signals | Destination |
|------|---------|-------------|
| \`idea\` | "what if", "we should", hypothesis | \`mewwiki/Operations/Ideas/inbox.md\` |
| \`decision\` | "we decided", "going with X" | \`mewwiki/Operations/Decisions/<project>-<slug>.md\` |
| \`person\` | observation about a specific person | \`mewwiki/Operations/People/<Name>.md\` |
| \`meeting\` | meeting notes, conversation summary | \`mewwiki/Operations/Meetings/_inbox/<slug>.md\` |
| \`api-note\` | API behaviour, endpoint quirk | current silo's \`wiki/<slug>.md\` |
| \`gotcha\` | something that burned time, non-obvious bug | current silo's \`wiki/<slug>.md\` |
| \`concept\` | definition, architecture decision | current silo's \`wiki/<slug>.md\` |

Design-silo \`decision\` dumps carry provenance: add frontmatter \`figma: <figma_file_key from Project_Status.md>\` plus the specific frame link if one was discussed this session. If the decision is visual and no frame is known, ask for the link before writing.

**2. Propose routing** — print in one block:
\`\`\`
Type:    <type>
Route:   <destination path>
Title:   <proposed title>
Project: <project or —>

Content preview:
<first 200 chars>

Confirm? [y/n/reclassify]
\`\`\`
Wait for confirmation before writing anything.

**3. Write** — after confirmation, write using matching template from \`mewwiki/Templates/\`. Add a \`[[wikilink]]\` back to the source project.

**4. Confirm** — print path written.`,
  },
  {
    pattern: /^new project\b/i,
    name: 'project-new',
    args: (prompt) => prompt.replace(/^new project\s*/i, '').trim(),
    instructions: (args) => `## Workflow: New Project

Slug hint from prompt: "${args || '(ask)'}"

**1. Gather info** (ask anything not provided above, all in one message):
- Slug (kebab-case)
- Full name (human-readable)
- Silo: \`software\`, \`design\`, or \`game\`
- Stack (if software): \`next\`, \`astro\`, or \`sveltekit\`
- North star: one sentence — what does "done" look like?
- Tier: \`pounce\` (small), \`stalk\` (multi-session), \`mewking\` (architecture)

**2. Scaffold** — run the appropriate command:
- Software: \`python mew.py new code-project <slug> --stack <stack>\`
- Design: \`python mew.py new ux-project <slug>\`
- Game: \`python mew.py new game-project <slug>\`

**3. Create mewwiki mirror** — read path from \`mewvault/.mewwiki\`. Create \`Projects/<slug>/index.md\` and \`Projects/<slug>/log.md\` immediately (don't wait for sync). Use today's date for \`last_session\` and \`synced\`.

**4. Update Brain/North Star.md** — append to Active Projects section:
\`- [[Projects/<slug>/index|<Full name>]] — <north star>\`

**5. Confirm**:
\`\`\`
Project created: <slug>
Silo: <silo path>
Wiki mirror: mewwiki/Projects/<slug>/
\`\`\``,
  },
  {
    pattern: /^(meeting[\s-]?prep|prep(are)? for)\b/i,
    name: 'meeting-prep',
    args: (prompt) => prompt.replace(/^(meeting[\s-]?prep|prep(are)? for)\s*/i, '').trim(),
    instructions: (args) => `## Workflow: Meeting Prep

Topic/person: "${args || '(ask)'}"

Read mewwiki path from \`mewvault/.mewwiki\`.

**1. Identify meeting** — if Google Calendar MCP is available, search for upcoming meetings matching the topic. Surface: date, time, attendees. If Calendar unavailable, ask.

**2. Load attendee profiles** — for each attendee, check \`mewwiki/Operations/People/<Name>.md\`. Note any missing profiles.

**3. Find last meeting note** — search \`mewwiki/Operations/Meetings/\` for most recent note matching topic or attendees. Extract: date, decisions, open action items (\`- [ ]\` lines).

**4. Load project context** (if relevant) — read \`Project_Status.md\` from the silo: current_phase, blockers, next_action.

**5. Output brief**:
\`\`\`
## Meeting Prep — <topic>
<date/time if known>

### Attendees
| Name | Role | Org |

### Last meeting (<date>)
Decisions: ...
Open items: ...

### Project context
Phase: ... | Blockers: ...

### Suggested agenda
1. <open item>
2. <current blocker>
\`\`\``,
  },
  {
    pattern: /^capture (the )?meeting\b/i,
    name: 'meeting-capture',
    instructions: `## Workflow: Meeting Capture

Read mewwiki path from \`mewvault/.mewwiki\`.

**1. Gather** (one message, skip anything already provided):
- Topic / meeting name
- Date (default: today)
- Attendees
- What was discussed / decided
- Action items

**2. Parse** — extract:
- Decisions: sentences with "we decided", "going with", "agreed to"
- Action items: format as \`- [ ] <task> — <owner>\`
- Person observations: notes about specific people

**3. Write meeting note** — create \`mewwiki/Operations/Meetings/YYYY-MM/<topic-slug>.md\` using Meeting Note template.

**4. File decisions** — for each decision, create \`mewwiki/Operations/Decisions/<project>-<slug>.md\`. Link back to the meeting note.

**5. Update People profiles** — for each person observation, append to \`mewwiki/Operations/People/<Name>.md\`.

**6. Update project wiki** (if applicable) — if meeting has an architectural/API decision, offer to write to the silo's \`wiki/\`.

**7. Confirm**:
\`\`\`
Meeting captured.
Note:      mewwiki/Operations/Meetings/YYYY-MM/<slug>.md
Decisions: <N> filed
People:    <names updated>
\`\`\``,
  },
  {
    pattern: /^ingest\s/i,
    name: 'ingest',
    args: (prompt) => prompt.replace(/^ingest\s+/i, '').trim(),
    instructions: (args) => `## Workflow: Ingest

Source file: "${args || '(list raw/ and ask)'}"

**1. Locate document** — if no path given, list files in current silo's \`raw/\` and ask which to ingest. Read the document (section by section if >500 lines).

**2. Discuss before writing** (mandatory — do NOT write files yet):
\`\`\`
I'd extract these concept pages from this document:

1. **<Title>** — <one-line description>
2. **<Title>** — <one-line description>
...

Does this breakdown look right? Any to add, remove, or merge?
\`\`\`
Wait for approval. Revise if asked.

**3. Write concept pages** (only after approval) — for each, write to current silo's \`wiki/<slug>.md\`:
\`\`\`markdown
---
title: <Title>
source: raw/<filename>
date: <today>
type: concept
---
# <Title>

## Summary
<2-4 sentence distillation>

## Key points
- ...

## Related
[[<related concept>]]
\`\`\`

**4. Update mewwiki Knowledge index** — append to \`mewwiki/Knowledge/index.md\` under \`## Concepts\`:
\`- [[Knowledge/concepts/<slug>|<Title>]] — <description> · (via <silo>/<project>, <date>)\`

**5. Confirm**: concept pages written, knowledge index updated, next sync info.`,
  },
];

function buildSessionCard(silo, agent, status, serviceResults, unwrapped, wikibrief) {
  const date = new Date().toISOString().slice(0, 10);

  const getField = (key) => {
    if (!status) return null;
    const m = status.match(new RegExp(`^${key}\\s*:\\s*(.+)$`, 'm'));
    return m ? m[1].trim() : null;
  };

  const tier = (getField('tier') || '—').toLowerCase();
  const phase = getField('current_phase') || '—';
  const planApproved = getField('plan_approved');
  const tierLabel = tier === 'mewking'
    ? `MewKing · plan ${planApproved === 'true' ? '✓ approved' : '✗ NEEDED'}`
    : tier.charAt(0).toUpperCase() + tier.slice(1);

  const svcLines = (serviceResults || []).map(r =>
    `  ${r.up ? '✓' : '✗'}  ${r.name}${r.up ? '' : ' — offline'}`
  );

  const flags = [];
  if (unwrapped && unwrapped.length) {
    const preview = unwrapped.slice(0, 2).join(', ') + (unwrapped.length > 2 ? `… +${unwrapped.length - 2}` : '');
    flags.push(`  ⚠  ${unwrapped.length} unwrapped session(s): ${preview}`);
  }
  if (wikibrief) {
    const inboxM = wikibrief.match(/Inbox:\s*(\d+)/);
    if (inboxM && parseInt(inboxM[1]) > 0) flags.push(`  ○  ${inboxM[1]} wiki inbox items pending`);
    const staleM = wikibrief.match(/Stale[^:]*:\s*(.+)/);
    if (staleM) {
      const count = staleM[1].split(',').length;
      flags.push(`  ○  ${count} stale project(s) (>14d idle)`);
    }
  }

  const allUp = (serviceResults || []).every(r => r.up);
  const statusBullet = allUp ? '● Ready' : '● Services offline — DeepSeek dispatch unavailable';

  const SEP = '══════════════════════════════════════════';
  return [
    SEP,
    ` MewVault  ·  ${silo || 'global'}  ·  ${date}`,
    SEP,
    ` Agent   ${agent.name} (${agent.model})`,
    ` Phase   ${phase}`,
    ` Tier    ${tierLabel}`,
    '',
    ' Services',
    ...(svcLines.length ? svcLines : ['  (none configured)']),
    ...(flags.length ? ['', ' Flags', ...flags] : []),
    '',
    ` ${statusBullet}`,
    SEP,
  ].join('\n');
}

function detectTrigger(prompt) {
  if (!prompt) return null;
  const trimmed = prompt.trim();
  for (const t of TRIGGERS) {
    if (t.pattern.test(trimmed)) {
      const args = t.args ? t.args(trimmed) : '';
      const instructions = typeof t.instructions === 'function'
        ? t.instructions(args)
        : t.instructions;
      return { name: t.name, instructions };
    }
  }
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
  const droppable = []; // section indexes safe to drop when over token budget (least important first)
  const agent = getAgent(silo);

  const sessionId = (input.session_id || '').replace(/[^a-zA-Z0-9-]/g, '') || 'nosession';
  const SESSION_FLAG = path.join(os.tmpdir(), `mew-shown-${sessionId}.flag`);
  const isFirstPrompt = !fs.existsSync(SESSION_FLAG);
  if (isFirstPrompt) { try { fs.writeFileSync(SESSION_FLAG, new Date().toISOString()); } catch {} }

  // Auto health check: run `mew doctor` detached on first prompt (never blocks the
  // session). Notifies via macOS notification on warn/fail and caches status for
  // the Vault Health section below. Skipped for doctor's own probe sessions.
  const isDoctorProbe = sessionId.startsWith('doctor-');
  if (isFirstPrompt && !isDoctorProbe) {
    try {
      const { spawn } = require('child_process');
      const child = spawn(
        process.platform === 'win32' ? 'python' : 'python3',
        [path.join(MEWVAULT_ROOT, 'mew.py'), 'doctor', '--quiet', '--notify'],
        { cwd: workspaceRoot, detached: true, stdio: 'ignore' }
      );
      child.unref();
    } catch {}
  }

  // On subsequent prompts, only emit conversational trigger instructions (if matched).
  // All context (rules, status, instincts, services) is already in the model's context window.
  if (!isFirstPrompt) {
    const trigger = detectTrigger(input.prompt);
    if (trigger) process.stdout.write(trigger.instructions + '\n');
    return;
  }

  // 1+2: Static rules (cache-eligible — always first)
  const rules = loadRules(workspaceRoot, silo);
  if (rules) sections.push('## Vault Rules\n\n' + rules);

  // 3: Active agent persona
  sections.push(
    `## Active Agent: ${agent.name} (${agent.model})\n\n` +
    `Silo: ${silo || 'global'} | Role: ${agent.role}`
  );

  // 3b: Dispatcher skill + routing index (mew-chief / global only)
  if (!silo || agent.name === 'mew-chief') {
    const dispatcher = loadAgentDispatcher(workspaceRoot);
    if (dispatcher) sections.push('## Agent Dispatch\n\n' + dispatcher);
  }

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
  if (instincts.json.length) {
    sections.push('## Active Vault Instincts\n\n' +
      instincts.json.map(i => `- [${i.silo || 'global'}] ${i.correct_behavior} (${i.confidence})`).join('\n'));
  }
  if (instincts.md.length) {
    sections.push('## Routing Rules\n\n' +
      instincts.md.map(i => `### ${i.name}\n\n${i.content}`).join('\n\n---\n\n'));
  }

  // 6b: Service health check
  const serviceResults = await checkServices(workspaceRoot);
  const servicesDisplay = serviceResults.map(r =>
    r.up
      ? `- ${r.name} (localhost:${r.port}): ✓ running`
      : `- ${r.name} (localhost:${r.port}): ✗ offline — ${r.detail}${r.hint ? ` · start: \`${r.hint}\`` : ''}`
  ).join('\n');
  sections.push('## Services\n\n' + servicesDisplay);

  // 6c: Vault health — cached result of the last `mew doctor` run (issues only)
  try {
    const docFile = path.join(workspaceRoot, '.claude', 'doctor-status.json');
    if (fs.existsSync(docFile)) {
      const doc = JSON.parse(fs.readFileSync(docFile, 'utf8'));
      if (doc.overall && doc.overall !== 'ok') {
        const issues = (doc.results || [])
          .filter(r => r.status !== 'ok')
          .map(r => `- [${r.status}] ${r.check}: ${r.message}`)
          .join('\n');
        sections.push(
          `## Vault Health — ${doc.overall.toUpperCase()} (mew doctor, ${doc.ran_at})\n\n` +
          issues + '\n\nMention these issues to the user in your first response. Fix or run `mew doctor` for details.'
        );
      }
    }
  } catch {}

  // 7: Semantic context from vector stores (Phase 4 — graceful degradation)
  const semantic = await loadSemanticContext(silo, workspaceRoot);
  if (semantic) { sections.push('## Relevant Context (semantic)\n\n' + semantic); droppable.push(sections.length - 1); }

  // 7b: MewVault memory recall (Phase 6 — SQLite FTS, graceful degradation)
  const memRecall = loadMemoryRecall(silo, workspaceRoot);
  if (memRecall) { sections.push('## Recent Context (mew memory)\n\n' + memRecall); droppable.push(sections.length - 1); }

  // 8: Open GitHub issues (Phase 6 — only when GITHUB_MCP_ENABLED=1 and github MCP configured)
  const githubIssues = await loadGithubIssues(silo, workspaceRoot, currentPhase);
  if (githubIssues) sections.push('## Open GitHub Issues (blocking current phase)\n\n' + githubIssues);

  // 9: MewWiki Brain brief (focus, inbox count, stale alerts)
  const wikibrief = loadMewWikiBrief(workspaceRoot);
  if (wikibrief) sections.push('## MewWiki\n\n' + wikibrief);

  // 10: Prior session context (.tmp loaded from ~/.claude/sessions/)
  if (process.env.MEW_SESSION_CONTEXT !== 'off') {
    const prior = loadPriorSession(cwd, workspaceRoot);
    if (prior) { sections.push('## Prior Session\n\n' + prior); droppable.push(sections.length - 1); }
  }

  // 11: MCP tool count warning
  const mcpCount = getMcpToolCount(workspaceRoot);
  if (mcpCount > 8) {
    sections.push(`⚠ ${mcpCount} MCP servers active (~${mcpCount * 15} tool slots). Run /context-budget to audit.`);
  }

  // 12: Model hint based on project tier
  const modelHint = getModelHint(status);
  if (modelHint) sections.push(modelHint);

  // 13: Conversational trigger + Session Card are must-keep — assembled outside
  // the truncatable brief so the budget can never sever them.
  const mustKeep = [];
  const trigger = detectTrigger(input.prompt);
  if (trigger) mustKeep.push(trigger.instructions);

  if (isFirstPrompt) {
    const card = buildSessionCard(silo, agent, status, serviceResults, unwrapped, wikibrief);
    mustKeep.push(
      '## Session Card\n\n' +
      'Display this status card verbatim as the very first thing in your response, before answering the user:\n\n' +
      '```\n' + card + '\n```'
    );
  }

  // Over budget: drop least-important sections whole (semantic recall, mew memory,
  // prior session) before falling back to a substring cut. Must-keep content is
  // reserved out of the budget first.
  const reserved = mustKeep.length ? mustKeep.join('\n\n---\n\n').length + 9 : 0;
  const budget = Math.max(MAX_CHARS - reserved, 1000);
  let brief = sections.join('\n\n---\n\n');
  for (const idx of droppable) {
    if (brief.length <= budget) break;
    sections[idx] = null;
    brief = sections.filter(Boolean).join('\n\n---\n\n');
  }
  if (brief.length > budget) {
    brief = brief.substring(0, budget) + '\n\n[... truncated to token budget]';
  }
  if (mustKeep.length) {
    brief = (brief.trim() ? brief + '\n\n---\n\n' : '') + mustKeep.join('\n\n---\n\n');
  }

  if (brief.trim()) process.stdout.write(brief + '\n');
}

main();
