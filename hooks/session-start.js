#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

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

// ---------------------------------------------------------------------------
// Conversational triggers — plain English replaces slash commands
// ---------------------------------------------------------------------------

const TRIGGERS = [
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

**3. Write log entry** — append to the project's \`log.md\` under \`## Entries\` (newest on top):
\`- **<today YYYY-MM-DD>** — <summary> [auto-wrap]\`
Update \`Project_Status.md\`: \`last_session\`, \`last_wrap\` = today; \`next_action\` = ask if not obvious.

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

  // 10: Prior session context (.tmp loaded from ~/.claude/sessions/)
  if (process.env.MEW_SESSION_CONTEXT !== 'off') {
    const prior = loadPriorSession(cwd, workspaceRoot);
    if (prior) sections.push('## Prior Session\n\n' + prior);
  }

  // 11: MCP tool count warning
  const mcpCount = getMcpToolCount(workspaceRoot);
  if (mcpCount > 8) {
    sections.push(`⚠ ${mcpCount} MCP servers active (~${mcpCount * 15} tool slots). Run /context-budget to audit.`);
  }

  // 12: Model hint based on project tier
  const modelHint = getModelHint(status);
  if (modelHint) sections.push(modelHint);

  // 13: Conversational trigger — inject workflow instructions if prompt matches
  const trigger = detectTrigger(input.prompt);
  if (trigger) sections.push(trigger.instructions);

  let brief = sections.join('\n\n---\n\n');
  if (brief.length > MAX_CHARS) {
    brief = brief.substring(0, MAX_CHARS) + '\n\n[... truncated to token budget]';
  }

  if (brief.trim()) process.stdout.write(brief + '\n');
}

main();
