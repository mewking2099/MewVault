# MewVault — Fresh Mac Setup

End goal: `cd ~/Jan && claude` → working vault with agent array, hooks, and wiki.

Estimated time: ~15 minutes.

---

## Step 1 — Xcode Command Line Tools

Open Terminal and run:

```bash
xcode-select --install
```

A dialog will pop up. Click **Install**. This gives you `git` and basic build tools.

---

## Step 2 — Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After it finishes, follow the **"Next steps"** it prints — usually adding Homebrew to your PATH.

---

## Step 3 — Node.js and Python

```bash
brew install node python@3.11
```

Verify:

```bash
node --version    # should be v18+
python3.11 --version
```

---

## Step 4 — Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Log in:

```bash
claude
```

Follow the browser auth flow. Once you see the Claude prompt, type `/exit` — we'll come back.

---

## Step 5 — Run the Bootstrap

```bash
curl -fsSL https://raw.githubusercontent.com/mewking2099/MewVault/main/bootstrap.sh | bash
```

This will:
- Create `~/Jan/` workspace
- Clone the MewVault tooling
- Install the `mew` CLI
- Create a fresh wiki scaffold at `~/Jan/mewwiki/`
- Wire up Claude Code hooks and rules

If you see any `⚠` warnings, read them — most are non-blocking.

---

## Step 6 — Store Your API Key

```bash
mew secret set ANTHROPIC_API_KEY
```

Paste your key when prompted. It's stored in `~/Jan/mewvault/secrets/` which is gitignored.

---

## Step 7 — Obsidian

1. Download Obsidian from [obsidian.md](https://obsidian.md) if you don't have it.
2. Open Obsidian → **Open folder as vault** → select `~/Jan/mewwiki`.
3. That's your personal knowledge base — it's empty and ready.

---

## Step 8 — First Session

Open a **new terminal tab** (so PATH changes take effect), then:

```bash
cd ~/Jan && claude
```

Once Claude starts, type:

```
standup
```

You should see a morning brief. The vault is live.

---

## What you now have

```
~/Jan/
  mewvault/        — mew CLI, agent array, hooks (git repo)
  mewwiki/         — your personal wiki (empty, yours to fill)
  software-projects/
  design-studio/
  game-lab/
  .claude/
    rules/         — Claude Code workspace rules (symlink → mewvault/bootstrap/rules/)
    settings.json  — hooks wired to mewvault
```

---

## Optional: Back up your wiki

Your wiki isn't connected to any remote yet. To back it up to GitHub:

```bash
cd ~/Jan/mewwiki
git init
git remote add origin https://github.com/<your-username>/mewwiki.git
git add . && git commit -m "init wiki"
git push -u origin main
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `mew: command not found` | Open a new terminal tab or run `source ~/.zshrc` |
| Hooks not firing | Make sure Node.js is installed: `node --version` |
| `claude: command not found` | Re-run: `npm install -g @anthropic-ai/claude-code` |
| Bootstrap fails at pip step | Try: `python3.11 -m pip install -e ~/Jan/mewvault` |
