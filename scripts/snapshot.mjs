#!/usr/bin/env node
// snapshot.mjs — visual regression snapshots for design/frontend projects.
//
// Usage: node mewvault/scripts/snapshot.mjs <project-root>
//
// Reads <project-root>/snapshot.routes.json:
//   { "baseUrl": "http://localhost:3000", "routes": ["/", "/pricing"], "viewports": [1440, 390] }
//
// Captures each route × viewport into assets/snapshots/<date>/, compares against
// the previous snapshot set (pixelmatch if installed, byte-hash otherwise), and
// writes assets/snapshots/snapshot-report.md.
//
// Requires: npm i -D playwright  (in the project, or globally)
// Exits 0 always — reporting tool, not a gate.

import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const projectRoot = process.argv[2] || process.cwd();
const configPath = path.join(projectRoot, 'snapshot.routes.json');

if (!fs.existsSync(configPath)) {
  console.log(`No snapshot.routes.json in ${projectRoot} — nothing to do.`);
  process.exit(0);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const baseUrl = config.baseUrl || 'http://localhost:3000';
const routes = config.routes || ['/'];
const viewports = config.viewports || [1440, 390];

const snapDir = path.join(projectRoot, 'assets', 'snapshots');
const today = new Date().toISOString().slice(0, 10);
const outDir = path.join(snapDir, today);

function slug(route) {
  return route === '/' ? 'home' : route.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '');
}

function previousSetDir() {
  if (!fs.existsSync(snapDir)) return null;
  const sets = fs.readdirSync(snapDir)
    .filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d) && d !== today)
    .sort();
  return sets.length ? path.join(snapDir, sets[sets.length - 1]) : null;
}

async function compare(prevFile, newFile) {
  // Try pixelmatch for a real diff; fall back to byte hash.
  try {
    const { default: pixelmatch } = await import('pixelmatch');
    const { PNG } = await import('pngjs');
    const a = PNG.sync.read(fs.readFileSync(prevFile));
    const b = PNG.sync.read(fs.readFileSync(newFile));
    if (a.width !== b.width || a.height !== b.height) return { changed: true, detail: 'dimensions changed' };
    const diffPixels = pixelmatch(a.data, b.data, null, a.width, a.height, { threshold: 0.1 });
    const pct = (diffPixels / (a.width * a.height)) * 100;
    return { changed: pct > 0.1, detail: `${pct.toFixed(2)}% pixels differ` };
  } catch {
    const h = f => createHash('sha256').update(fs.readFileSync(f)).digest('hex');
    const changed = h(prevFile) !== h(newFile);
    return { changed, detail: changed ? 'content hash differs (install pixelmatch+pngjs for % diff)' : 'identical' };
  }
}

async function main() {
  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch {
    console.log('Playwright not installed — skipping snapshots. Install: npm i -D playwright && npx playwright install chromium');
    process.exit(0);
  }

  fs.mkdirSync(outDir, { recursive: true });
  const prev = previousSetDir();
  const browser = await chromium.launch();
  const report = [`# Snapshot report — ${today}`, '', `Base: ${baseUrl}`, ''];
  let changedCount = 0;

  for (const route of routes) {
    for (const vw of viewports) {
      const name = `${slug(route)}-${vw}.png`;
      const outFile = path.join(outDir, name);
      try {
        const page = await browser.newPage({ viewport: { width: vw, height: 900 } });
        await page.goto(baseUrl + route, { waitUntil: 'networkidle', timeout: 20000 });
        await page.screenshot({ path: outFile, fullPage: true });
        await page.close();
      } catch (e) {
        report.push(`- ✗ ${route} @${vw}: capture failed (${e.message.split('\n')[0]})`);
        continue;
      }
      if (prev && fs.existsSync(path.join(prev, name))) {
        const { changed, detail } = await compare(path.join(prev, name), outFile);
        if (changed) changedCount++;
        report.push(`- ${changed ? '≠ CHANGED' : '= same'} ${route} @${vw} — ${detail}`);
      } else {
        report.push(`- + new ${route} @${vw} (no previous snapshot)`);
      }
    }
  }

  await browser.close();
  report.push('', prev ? `Compared against: ${path.basename(prev)}` : 'First snapshot set — nothing to compare.',
    `Changed: ${changedCount}`);
  fs.writeFileSync(path.join(snapDir, 'snapshot-report.md'), report.join('\n') + '\n', 'utf8');
  console.log(report.join('\n'));

  // Keep only the 5 most recent snapshot sets
  const sets = fs.readdirSync(snapDir).filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort();
  for (const old of sets.slice(0, -5)) {
    fs.rmSync(path.join(snapDir, old), { recursive: true, force: true });
  }
}

main();
