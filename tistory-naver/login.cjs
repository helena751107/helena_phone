/**
 * login.cjs — Naver 쿠키 추출 v2.0 (PC-native)
 *
 * - ADB/Termux 의존성 완전 제거
 * - Windows Chrome + Playwright headless=False
 * - 계정별 독립 프로파일 (쿠키 오염 없음)
 * - 자동 로그인 실패 시 수동 대기 60초
 *
 * 사용법:
 *   node login.cjs [parksy_kr|dtslib|eae_kr|all]
 */

'use strict';

const path = require('path');
const fs   = require('fs');
const { chromium } = require('playwright');

const __dir       = __dirname;
const CREDS_PATH  = path.join(__dir, 'accounts', 'credentials.json');
const COOKIES_DIR = path.join(__dir, 'accounts', 'cookies');

// Chrome 프로필은 Linux 파일시스템에 저장 (NTFS /mnt/d/ 에서 SingletonLock 생성 불가)
const PROF_BASE   = path.join(process.env.HOME || '/root', '.dtslib-naver-profiles');

fs.mkdirSync(COOKIES_DIR, { recursive: true });
fs.mkdirSync(PROF_BASE,   { recursive: true });

const { accounts, password } = JSON.parse(fs.readFileSync(CREDS_PATH, 'utf8'));

const accountId = process.argv[2];
if (!accountId) {
  console.log('사용법: node login.cjs [parksy_kr|dtslib|eae_kr|all]');
  process.exit(1);
}

const targets = accountId === 'all'
  ? accounts
  : accounts.filter(a => a.id === accountId);

if (!targets.length) {
  console.log(`계정 없음: ${accountId}`);
  process.exit(1);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// 015에서 실전 검증된 ncaptcha 질문 추출 (innerText 파싱)
function parseQuestion(bodyText) {
  const lines = bodyText.split('\n').map(l => l.trim()).filter(Boolean);
  const startIdx = lines.findIndex(l => l.includes('가상으로 제작된'));
  const endIdx   = lines.findIndex(l => l.includes('새로고침'));
  if (startIdx >= 0 && endIdx > startIdx) {
    return lines.slice(startIdx + 1, endIdx).join(' ');
  }
  return lines.find(l =>
    l.includes('몇') || l.includes('[?]') || l.includes('이름') || l.includes('채워')
  ) || '';
}

// 캡차 발생 시 Claude 연동 파이프라인
// SCREENSHOT/QUESTION/ANSWER_FILE 출력 → Claude가 읽고 답 파일 작성 → 자동 제출
async function handleCaptcha(page, accId, waitSec = 120) {
  const bodyText  = await page.innerText('body').catch(() => '');
  const question  = parseQuestion(bodyText);
  const shotPath  = `/tmp/naver_cap_${accId}.png`;
  const ansPath   = `/tmp/naver_ans_${accId}.txt`;

  await page.screenshot({ path: shotPath });
  console.log(`  SCREENSHOT:${shotPath}`);
  console.log(`  QUESTION:${question || '(스크린샷 확인)'}`);
  console.log(`  ANSWER_FILE:${ansPath}`);
  console.log(`  → echo "답" > ${ansPath}  으로 답 입력 (${waitSec}초 대기)`);

  for (let i = 0; i < waitSec; i++) {
    await sleep(1000);
    if (fs.existsSync(ansPath)) {
      const ans = fs.readFileSync(ansPath, 'utf8').trim();
      fs.unlinkSync(ansPath);
      if (ans) {
        console.log(`  SUBMITTING:${ans}`);
        const el = await page.$('#captcha, input[name="captcha"], input[placeholder*="정답"]');
        if (el) { await el.fill(ans); await sleep(300); }
        await page.click('.btn_login, button[type="submit"]').catch(() => page.keyboard.press('Enter'));
        await sleep(3000);
        return true;
      }
    }
  }
  console.log(`  CAPTCHA_TIMEOUT:${accId}`);
  return false;
}

async function naverLogin(page, naverId, pw, accId) {
  console.log(`  로그인 시도: ${naverId}`);
  await page.goto('https://nid.naver.com/nidlogin.login',
    { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(2000);

  // IP보안 OFF: evaluate로 텍스트 기반 탐색 후 클릭
  try {
    const toggled = await page.evaluate(() => {
      const all = document.querySelectorAll('button, a, label, span');
      for (const el of all) {
        if (el.textContent && el.textContent.includes('IP보안')) {
          el.click();
          return true;
        }
      }
      return false;
    });
    if (toggled) { await sleep(600); console.log('  IP보안 클릭'); }
  } catch(e) {}

  // ID 입력 (fill)
  await page.click('#id');
  await page.fill('#id', naverId);
  await sleep(400);

  await page.click('#pw');
  await sleep(300);
  await page.keyboard.type(pw, { delay: 80 });
  const pwVal = await page.evaluate(() => document.querySelector('#pw')?.value || '');
  console.log(`  PW check: "${pwVal.length > 0 ? '●'.repeat(pwVal.length) : '(비어있음)'}" (${pwVal.length}자)`);
  await sleep(400);

  // 로그인 버튼 클릭
  const loginBtn = await page.$('.btn_login, button[type="submit"], #log\\.login');
  if (loginBtn) {
    await loginBtn.click();
  } else {
    await page.keyboard.press('Enter');
  }
  await sleep(5000);

  for (let i = 0; i < 10; i++) {
    const url = page.url();
    if (url.includes('naver.com') && !url.includes('nidlogin') && !url.includes('captcha')) {
      console.log(`  ✅ 자동 로그인 성공`);
      return true;
    }
    await sleep(1000);
  }

  console.log(`\n  ⚠ 자동 로그인 실패 → 캡차 파이프라인 시도`);
  // 1차: Claude 연동 캡차 파이프라인 (120초)
  const captchaOk = await handleCaptcha(page, accId || naverId, 120);
  if (captchaOk) {
    const urlAfter = page.url();
    if (urlAfter.includes('naver.com') && !urlAfter.includes('nidlogin')) {
      console.log(`  ✅ 캡차 처리 후 로그인 성공`);
      return true;
    }
  }

  // 2차: 수동 폴백 (10분)
  console.log(`  👉 [${naverId}] Chrome 창에서 직접 로그인하세요 (10분 대기)\n`);
  for (let i = 0; i < 600; i++) {
    await sleep(1000);
    const url = page.url();
    if (url.includes('naver.com') && !url.includes('nidlogin') && !url.includes('captcha')) {
      console.log(`  ✅ 수동 로그인 성공 [${naverId}] (${i + 1}초)`);
      return true;
    }
    if (i % 60 === 59) console.log(`  [${naverId}] ... ${Math.floor((600 - i - 1) / 60)}분 ${(600 - i - 1) % 60}초 남음`);
  }

  console.log(`  ❌ 로그인 최종 실패: ${naverId}`);
  return false;
}

async function processAccount(acc) {
  const naverId = acc.naver_id;
  const pw      = acc.password;
  const profDir = path.join(PROF_BASE, acc.id);

  console.log(`\n${'='.repeat(50)}\n계정: ${naverId}`);

  const ctx = await chromium.launchPersistentContext(profDir, {
    executablePath: '/home/dtsli/.cache/ms-playwright/chromium-1212/chrome-linux64/chrome',
    headless: false,
    viewport: { width: 1280, height: 900 },
    locale:   'ko-KR',
    args:     ['--no-first-run', '--no-default-browser-check', '--no-sandbox'],
  });

  const page = ctx.pages()[0] || await ctx.newPage();

  try {
    await page.goto('https://www.naver.com', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(2000);

    const isLoggedIn = await page.evaluate(() =>
      !!document.querySelector('.gnb_my, .MyView-module__link_avatar, [class*="avatar"]')
    );

    if (!isLoggedIn) {
      const ok = await naverLogin(page, naverId, pw, acc.id);
      if (!ok) return;
    } else {
      console.log(`  이미 로그인 상태`);
    }

    const cookies     = await ctx.cookies(['https://naver.com', 'https://blog.naver.com']);
    const naverCookies = cookies.filter(c => c.domain?.includes('naver.com'));
    const authCookies  = naverCookies.filter(c => ['NID_AUT', 'NID_SES', 'NID_JKL'].includes(c.name));

    if (!authCookies.length) {
      console.log(`  ⚠ 인증 쿠키 없음 — 보유: ${naverCookies.map(c => c.name).join(', ')}`);
    } else {
      console.log(`  ✅ ${authCookies.map(c => c.name).join(', ')}`);
    }

    const cookiePath = acc.cookies_file
      ? path.join(__dir, acc.cookies_file)
      : path.join(COOKIES_DIR, `${acc.id}.json`);

    fs.mkdirSync(path.dirname(cookiePath), { recursive: true });

    // 세션 쿠키(expires=-1) expires 보정 — 브라우저 재시작 후에도 유지
    const now = Math.floor(Date.now() / 1000);
    const fixedCookies = naverCookies.map(c => ({
      ...c,
      expires: c.expires === -1 ? now + 86400 * 7 : c.expires
    }));
    fs.writeFileSync(cookiePath, JSON.stringify(fixedCookies, null, 2), 'utf8');
    console.log(`  쿠키 저장: ${cookiePath} (expires 보정 완료)`);

    // storageState도 expires 보정
    await ctx.storageState({ path: path.join(COOKIES_DIR, `${acc.id}_state.json`) });
    try {
      const ss = JSON.parse(fs.readFileSync(path.join(COOKIES_DIR, `${acc.id}_state.json`), 'utf8'));
      if (ss.cookies) {
        ss.cookies = ss.cookies.map(c => ({
          ...c,
          expires: c.expires === -1 ? now + 86400 * 7 : c.expires
        }));
        fs.writeFileSync(path.join(COOKIES_DIR, `${acc.id}_state.json`), JSON.stringify(ss, null, 2), 'utf8');
        console.log(`  storageState 보정 완료`);
      }
    } catch (e) {
      console.log(`  ⚠ storageState 보정 실패: ${e.message}`);
    }

  } catch (e) {
    console.log(`  오류: ${e.message}`);
  } finally {
    await ctx.close();
  }
}

(async () => {
  console.log('=== Naver 쿠키 추출 v2.0 (PC-native) ===');
  console.log(`계정 ${targets.length}개 동시 실행 — Chrome 창 ${targets.length}개 뜹니다\n`);
  // 전체 계정 동시 실행
  await Promise.all(
    targets.map(acc => processAccount({ ...acc, password: acc.password || password }))
  );
  console.log('\n완료');
})();
