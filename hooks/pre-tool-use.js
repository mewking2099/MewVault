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

  // Sub-logic E: TDD gate (warning only)
  if (filePath && ['Write', 'Edit'].includes(toolName)) {
    const ext = path.extname(filePath);
    const inSrc = normPath(filePath).match(/\/(src|lib)\//);
    if (inSrc && ['.js', '.ts', '.py', '.go', '.rs'].includes(ext)) {
      const base = path.basename(filePath, ext);
      const dir = path.dirname(filePath);
      const testExists = [
        `${base}.test${ext}`, `${base}.spec${ext}`,
        `__tests__/${base}.test${ext}`, `tests/${base}${ext}`,
      ].some(t => fs.existsSync(path.join(dir, t)) || fs.existsSync(path.join(dir, '..', t)));
      if (!testExists) {
        process.stderr.write(`⚠ TDD: No test file found for ${path.basename(filePath)}. Consider writing tests first.\n`);
      }
    }
  }

  process.exit(0);
}

main();
