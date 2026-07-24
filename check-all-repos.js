#!/usr/bin/env node
// 5개 레포 GitHub Pages + GitHub README 스크린샷
const { chromium } = require('playwright');

const REPOS = [
  { name: '📱 helena_phone',   page: 'https://helena751107.github.io/helena_phone/',    git: 'https://github.com/helena751107/helena_phone' },
  { name: '🗃️ helana_log',     page: 'https://helena751107.github.io/helana_log/',       git: 'https://github.com/helena751107/helana_log' },
  { name: '✝️ helana-faith',   page: 'https://helena751107.github.io/helana-faith/',     git: 'https://github.com/helena751107/helana-faith' },
  { name: '🎹 helena-piano',   page: 'https://helena751107.github.io/helena-piano/',     git: 'https://github.com/helena751107/helena-piano' },
  { name: '🧠 helena-psycare', page: 'https://helena751107.github.io/helena-psycare/',   git: 'https://github.com/helena751107/helena-psycare' },
];

const CHECKS = {
  helena_phone:   ['README.md', 'GUIDE.md', 'CHRONICLE.md', '01-foundation', '02-network', '03-broadcast', '04-phone-control', '05-optimization', 'configs', 'scripts', '_notebook', 'notebook'],
  helana_log:     ['README.md', 'apk', 'schema', 'logs', 'mcp-server', 'scripts', 'docs'],
  'helana-faith': ['README.md', 'chronicle', 'theology', 'comparative-religion', 'family', 'liturgy', 'writings'],
  'helena-piano': ['README.md', 'scores', 'midi', 'audio-generation', 'reaper-projects', 'python-tools', 'samples', 'sheet-music', 'practice', 'github-actions', 'docs'],
  'helena-psycare': ['README.md', 'psychoanalysis', 'psychopathology', 'psychotherapy', 'diagnostics', 'research', 'mcp-model', 'beautiful-mind', 'family-history', 'resources', 'docs'],
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });

  console.log('\n══════════════════════════════════════════════════');
  console.log('  5개 레포 전수 검사 — Playwright 스크린샷');
  console.log('══════════════════════════════════════════════════\n');

  for (const repo of REPOS) {
    const key = repo.page.split('/').filter(Boolean).pop().split('.')[0];
    const slug = key === 'helena-psycare' ? 'helena-psycare' : key === 'helana-faith' ? 'helana-faith' : key;
    console.log(`\n━━━ ${repo.name} ━━━`);

    // 1. GitHub Pages 스크린샷
    try {
      const page = await context.newPage();
      await page.goto(repo.page, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(1500);
      const title = await page.title();
      console.log(`  🌐 Pages:   ${repo.page}`);
      console.log(`  📌 Title:   ${title}`);
      const h1 = await page.locator('h1').first().textContent().catch(() => '?');
      console.log(`  📰 H1:      ${h1.slice(0, 60)}`);
      await page.screenshot({ path: `/tmp/screen-${key}-pages.png`, fullPage: true });
      const size = (await page.evaluate(() => document.body.scrollHeight));
      console.log(`  📐 Height:  ${size}px`);
      await page.close();
    } catch (e) {
      console.log(`  ❌ Pages:   ${e.message.slice(0, 80)}`);
    }

    // 2. GitHub README 스크린샷
    try {
      const page = await context.newPage();
      await page.goto(repo.git, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(1500);
      const readme = await page.locator('article.markdown-body').first().isVisible().catch(() => false);
      console.log(`  📖 README:  ${readme ? '✅ 표시됨' : '⚠️ 안 보임'}`);
      const repoName = await page.locator('strong[itemprop="name"] a').first().textContent().catch(() => '?');
      console.log(`  📁 Repo:    ${repoName}`);
      await page.screenshot({ path: `/tmp/screen-${key}-github.png`, fullPage: true });
      await page.close();
    } catch (e) {
      console.log(`  ❌ GitHub:  ${e.message.slice(0, 80)}`);
    }

    // 3. 디렉토리 구조 확인
    const expected = CHECKS[slug];
    if (expected) {
      console.log(`  📂 검증할 항목: ${expected.length}개`);
      for (const item of expected) {
        try {
          const page = await context.newPage();
          const resp = await page.goto(`${repo.git}/tree/main/${item}`, { waitUntil: 'domcontentloaded', timeout: 10000 });
          const status = resp?.status() || 0;
          if (status === 200) console.log(`    ✅ ${item}`);
          else if (status === 404) console.log(`    ❌ ${item} — 404 Not Found`);
          else console.log(`    ⚠️ ${item} — HTTP ${status}`);
          await page.close();
        } catch (e) {
          console.log(`    ⚠️ ${item} — ${e.message.slice(0, 50)}`);
        }
      }
    }
  }

  // 4. Pages 상태 개요
  console.log('\n━━━ 전체 Pages 상태 ━━━');
  for (const repo of REPOS) {
    try {
      const page = await context.newPage();
      const resp = await page.goto(repo.page, { waitUntil: 'domcontentloaded', timeout: 10000 });
      const code = resp?.status() || 0;
      const ok = code === 200 || code === 304;
      console.log(`  ${ok ? '✅' : '❌'} ${repo.page} → HTTP ${code}`);
      await page.close();
    } catch (e) {
      console.log(`  ❌ ${repo.page} → ${e.message.slice(0, 50)}`);
    }
  }

  await browser.close();

  console.log('\n══════════════════════════════════════════════════');
  console.log('  검사 완료 — 스크린샷: /tmp/screen-*.png');
  console.log('══════════════════════════════════════════════════\n');
})();
