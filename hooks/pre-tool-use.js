#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');

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

function findProjectStatus(cwd, workspaceRoot) {
  let dir = path.resolve(cwd);
  while (dir.length >= workspaceRoot.length) {
    const f = path.join(dir, 'Project_Status.md');
    if (fs.existsSync(f)) {
      const txt = fs.readFileSync(f, 'utf8');
      const get = (key) => { const m = txt.match(new RegExp(`^${key}:\\s*(.+)$`, 'm')); return m ? m[1].trim() : null; };
      return {
        path: f,
        content: txt,
        tier: get('tier'),
        planApproved: get('plan_approved') === 'true',
        gateBlockCount: parseInt(get('gate_block_count') || '0', 10),
      };
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function getMewWikiPath(workspaceRoot) {
  const pointer = path.join(workspaceRoot, 'mewvault', '.mewwiki');
  if (!fs.existsSync(pointer)) return null;
  try { return fs.readFileSync(pointer, 'utf8').trim() || null; } catch { return null; }
}

const SECRET_PATTERNS = [
  /sk-[a-zA-Z0-9]{20,}/,
  /ghp_[a-zA-Z0-9]{36}/,
  /AKIA[A-Z0-9]{16}/,
  /(?:API_KEY|ANTHROPIC_API_KEY|OPENAI_API_KEY)\s*=\s*[^\s'"]{8,}/,
  /(?:password|passwd)\s*=\s*[^\s'"]{4,}/i,
];

function block(msg) {
  process.stderr.write(msg + '\n');
  process.exit(2);
}

function normPath(p) {
  return (p || '').replace(/\\/g, '/');
}

function main() {
  const input = readStdin();
  const toolName = input.tool_name || '';
  const toolInput = input.tool_input || {};
  const cwd = input.cwd || process.cwd();

  const filePath = normPath(toolInput.file_path || toolInput.path || '');
  const content = toolInput.content || toolInput.new_string || '';

  // Sub-logic D: Immutable paths (fast-fail first)
  if (filePath.includes('/raw/') || filePath.includes('\\raw\\')) {
    block('⛔ MewVault: raw/ sources are immutable. Never write here.');
  }
  if (filePath.includes('/.obsidian/') || filePath.includes('\\.obsidian\\')) {
    block('⛔ MewVault: .obsidian/ is off-limits. Use Obsidian to change settings.');
  }

  // Sub-logic F: mewwiki direct write guard
  if (filePath && ['Write', 'Edit', 'MultiEdit'].includes(toolName)) {
    const workspaceRoot = findWorkspaceRoot(cwd);
    const wikiPath = getMewWikiPath(workspaceRoot);
    if (wikiPath) {
      const norm = (p) => p.replace(/\\/g, '/').replace(/\/$/, '');
      if (norm(filePath).startsWith(norm(wikiPath) + '/')) {
        block(
          '⛔ MewVault: Do not write to mewwiki/ directly.\n' +
          'Sync from silos:  mew wiki sync\n' +
          'Route a note:     /dump <content>'
        );
      }
    }
  }

  // Sub-logic C: Secrets guardian
  const inSecrets = filePath.includes('/secrets/') || filePath.includes('\\secrets\\');
  if (!inSecrets && content && SECRET_PATTERNS.some(p => p.test(content))) {
    block('⛔ MewVault: Secret detected outside secrets/.\nUse: mew secret set KEY_NAME');
  }

  // Sub-logic A: MewKing gate (only for write operations with a file path)
  if (filePath && ['Write', 'Edit', 'MultiEdit'].includes(toolName)) {
    const workspaceRoot = findWorkspaceRoot(cwd);
    const status = findProjectStatus(cwd, workspaceRoot);

    if (status && status.tier === 'MewKing' && !status.planApproved) {
      const newCount = status.gateBlockCount + 1;

      // Increment gate_block_count in Project_Status.md
      let updated = status.content;
      if (/^gate_block_count:/m.test(updated)) {
        updated = updated.replace(/^gate_block_count:\s*\d+/m, `gate_block_count: ${newCount}`);
      } else {
        updated = updated.replace(/^(plan_approved:)/m, `gate_block_count: ${newCount}\n$1`);
      }
      try { fs.writeFileSync(status.path, updated, 'utf8'); } catch {}

      // Write REVIEW_REQUIRED.md after 2 blocks
      if (newCount >= 2) {
        const reviewDir = path.join(path.dirname(status.path), 'proposals', 'active');
        try {
          fs.mkdirSync(reviewDir, { recursive: true });
          fs.writeFileSync(
            path.join(reviewDir, 'REVIEW_REQUIRED.md'),
            `# Review Required\n\nMewKing gate triggered ${newCount} times. Approve plan.md before continuing.\n`,
            'utf8'
          );
        } catch {}
      }

      block(
        `⛔ MewKing Gate: plan.md not approved (blocked ${newCount}×).\n` +
        `Approve proposals/active/<feature>/plan.md before writing code.`
      );
    }
  }

  // Sub-logic B: GateGuard — warn on first write to a file this session
  // (warning only — exit 0, stderr message)
  if (filePath && ['Write', 'Edit'].includes(toolName)) {
    const workspaceRoot = findWorkspaceRoot(cwd);
    const sessionStateFile = path.join(workspaceRoot, '.claude', 'gateguard-session.json');
    let seen = [];
    if (fs.existsSync(sessionStateFile)) {
      try { seen = JSON.parse(fs.readFileSync(sessionStateFile, 'utf8')); } catch {}
    }
    if (!seen.includes(filePath)) {
      seen.push(filePath);
      try {
        fs.mkdirSync(path.dirname(sessionStateFile), { recursive: true });
        fs.writeFileSync(sessionStateFile, JSON.stringify(seen), 'utf8');
      } catch {}
      // Warn for files not inside the current project (cross-project write)
      // This is a lightweight check — full GateGuard needs transcript access
    }
  }

  // Sub-logic G: Write size guard
  if (toolName === 'Write' && content) {
    const limitsFile = path.join(findWorkspaceRoot(cwd), '.claude', 'limits.json');
    let warnChars = 40000;
    let blockChars = 200000;
    try {
      const lim = JSON.parse(fs.readFileSync(limitsFile, 'utf8'));
      if (lim.write_warn_chars) warnChars = lim.write_warn_chars;
      if (lim.write_block_chars) blockChars = lim.write_block_chars;
    } catch {}
    if (content.length > blockChars) {
      block(`⛔ MewVault: Write too large (${Math.round(content.length / 1000)}k chars ≈ ${Math.round(content.length / 4000)}k tokens).\nBreak this into smaller writes or use Edit for targeted changes.`);
    } else if (content.length > warnChars) {
      process.stderr.write(`⚠ MewVault: Large write (${Math.round(content.length / 1000)}k chars ≈ ${Math.round(content.length / 4000)}k tokens). Consider using Edit for targeted changes.\n`);
    }
  }

  // Sub-logic D2: Audit-score gate (design silo).
  // A design project cannot move to handoff/delivery while open_p0 > 0.
  // Same enforcement philosophy as the MewKing gate.
  if (filePath && path.basename(filePath) === 'Project_Status.md' &&
      normPath(filePath).includes('/design-studio/') &&
      ['Write', 'Edit'].includes(toolName)) {
    const newContent = toolInput.content || toolInput.new_string || '';
    if (/current_phase\s*:\s*.*(handoff|delivery)/i.test(newContent)) {
      let openP0 = 0;
      // Prefer the value in the incoming content; fall back to the file on disk
      const inNew = newContent.match(/^open_p0\s*:\s*(\d+)/m);
      if (inNew) {
        openP0 = parseInt(inNew[1], 10);
      } else if (fs.existsSync(filePath)) {
        const cur = fs.readFileSync(filePath, 'utf8').match(/^open_p0\s*:\s*(\d+)/m);
        if (cur) openP0 = parseInt(cur[1], 10);
      }
      if (openP0 > 0) {
        block(
          `⛔ Audit gate: ${openP0} open P0 finding(s) — cannot move this design project to handoff/delivery.\n` +
          `Fix the P0s, re-run /impeccable audit, update open_p0 in Project_Status.md, then advance the phase.`
        );
      }
    }
  }

  // Sub-logic D3: Confidentiality gate (career-studio, later content-studio).
  // A case study cannot become `publishable` until `confidentiality: cleared`
  // (owner-approved named-entities checklist). Enforcement, not advice.
  if (filePath && ['Write', 'Edit'].includes(toolName) &&
      /\/(career-studio|content-studio)\//.test(normPath(filePath)) &&
      path.extname(filePath) === '.md') {
    const newContent = toolInput.content || toolInput.new_string || '';
    if (/status\s*:\s*publishable/i.test(newContent)) {
      let cleared = /confidentiality\s*:\s*cleared/i.test(newContent);
      if (!cleared && fs.existsSync(filePath)) {
        cleared = /confidentiality\s*:\s*cleared/i.test(fs.readFileSync(filePath, 'utf8'));
      }
      if (!cleared) {
        block(
          `⛔ Confidentiality gate: cannot set status: publishable while confidentiality is not 'cleared'.\n` +
          `Extract every client/employer name, metric, and internal detail from the draft, present the ` +
          `keep/anonymize/remove checklist, get the owner's approval on each item, set ` +
          `'confidentiality: cleared' — then mark publishable.`
        );
      }
    }
  }

  // Sub-logic D4: Trading journal + backtest immutability (learn-lab).
  // Append-only files: Edit is always blocked; Write is blocked once the file
  // exists (appends happen via bash `>>`). Corrections are new entries.
  if (filePath &&
      /\/learn-lab\/trading\/(journal|backtests)\//.test(normPath(filePath)) &&
      ['Write', 'Edit', 'MultiEdit'].includes(toolName)) {
    if (toolName !== 'Write' || fs.existsSync(filePath)) {
      block(
        `⛔ Journal immutability: ${path.basename(filePath)} is append-only.\n` +
        `Append entries via bash: echo '<json>' >> <file>. Corrections are NEW entries ` +
        `referencing the original — history is never rewritten.`
      );
    }
  }

  // Sub-logic E: TDD gate.
  // HARD BLOCK for stalk/mewking projects (audit 2026-07-08: the old stderr
  // warning had 0% compliance — PreToolUse stderr never reaches Claude on exit 0).
  // Warning-only for pounce. Opt out per project with `tdd: off` in Project_Status.md.
  // UI component files (.tsx/.jsx/.vue/.svelte/.astro) are exempt — they're covered
  // by the Impeccable gauntlet instead.
  if (filePath && ['Write', 'Edit'].includes(toolName) && !/\.(test|spec)\./.test(filePath)) {
    const ext = path.extname(filePath);
    const inSrc = normPath(filePath).match(/\/(src|lib)\//);
    if (inSrc && ['.js', '.ts', '.py', '.go', '.rs'].includes(ext)) {
      const base = path.basename(filePath, ext);
      const dir = path.dirname(filePath);
      const testExists = [
        `${base}.test${ext}`, `${base}.spec${ext}`,
        `__tests__/${base}.test${ext}`, `tests/${base}${ext}`,
        `${base}.test.ts`, `${base}.spec.ts`,
      ].some(t =>
        fs.existsSync(path.join(dir, t)) ||
        fs.existsSync(path.join(dir, '..', t)) ||
        fs.existsSync(path.join(dir, '..', '..', 'tests', t)));
      if (!testExists) {
        const wsRoot = findWorkspaceRoot(input.cwd || process.cwd());
        const status = findProjectStatus(path.dirname(filePath), wsRoot);
        const tier = ((status && status.tier) || '').toLowerCase();
        const tddOff = status && /^tdd:\s*off/m.test(status.content);
        if (['stalk', 'mewking'].includes(tier) && !tddOff) {
          block(
            `⛔ TDD gate (${tier} tier): no test file exists for ${path.basename(filePath)}.\n` +
            `Write the test FIRST — derive cases from the spec's acceptance criteria ` +
            `(specs/<feature>.md), then implement until it passes.\n` +
            `Expected: ${base}.test${ext} next to the file or in tests/.\n` +
            `Project opt-out (owner decision only): add 'tdd: off' to Project_Status.md.`
          );
        } else {
          process.stderr.write(`⚠ TDD: No test file found for ${path.basename(filePath)}. Consider writing tests first.\n`);
        }
      }
    }
  }

  process.exit(0);
}

main();
