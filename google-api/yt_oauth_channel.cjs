/**
 * yt_oauth_channel.cjs — 채널별 전용 OAuth 토큰 발급 (yt_oauth_auto.cjs 일반화)
 * Chrome(실제 프로필) → YouTube Studio에서 대상 채널로 전환 → OAuth 동의 → Allow
 * 결과: accounts/token_a__<채널slug>.json 저장
 *
 * 배경: upload.cjs가 onBehalfOfContentOwnerChannel(CMS 전용 파라미터)로
 * 브랜드 채널 라우팅을 시도하다 "invalid argument" 에러 발생 (2026-07 확인).
 * 실제 해법: 채널마다 OAuth 콘센트 시 그 채널을 선택해서 받은 전용 토큰을 쓴다.
 *
 * 사용법: node yt_oauth_channel.cjs @musician-parksy
 */
'use strict';

const { chromium } = require('playwright');
const { google }   = require('googleapis');
const http  = require('http');
const url   = require('url');
const fs    = require('fs');
const path  = require('path');

const __dir       = __dirname;
const SECRET_PATH = path.join(__dir, 'client_secret.json');
const CHANNELS_PATH = path.join(__dir, 'accounts', 'channels.json');

const SCOPES = [
  'https://www.googleapis.com/auth/youtube',
  'https://www.googleapis.com/auth/yt-analytics.readonly',
  'https://www.googleapis.com/auth/spreadsheets',
  'https://www.googleapis.com/auth/drive.file'
];

const channelHandle = process.argv[2];
if (!channelHandle) {
  console.log('사용법: node yt_oauth_channel.cjs @musician-parksy');
  process.exit(1);
}

const channelsData = JSON.parse(fs.readFileSync(CHANNELS_PATH));
let accountEmail, accountId, channelId, channelSlug;
for (const acc of channelsData.accounts) {
  const ch = acc.channels.find(c => c.handle === channelHandle);
  if (ch) {
    accountEmail = acc.email;
    accountId    = acc.id;
    channelId    = ch.channel_id;
    channelSlug  = ch.handle.replace(/^@/, '');
    break;
  }
}
if (!channelId) {
  console.log(`channels.json에서 ${channelHandle} 못 찾음`);
  process.exit(1);
}

const TOKEN_PATH = path.join(__dir, 'accounts', `token_${accountId}__${channelSlug}.json`);
const PASSWORD   = process.env.PASSWORD || '<PASSWORD>';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function switchToChannel(page) {
  console.log(`\n[채널 전환] YouTube Studio → ${channelHandle} (${channelId})...`);
  for (let i = 0; i < 3; i++) {
    try {
      await page.goto('https://studio.youtube.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
      break;
    } catch (e) {
      console.log(`  goto 실패 (시도 ${i + 1}/3): ${e.message.slice(0, 120)}`);
      if (i === 2) throw e;
      await sleep(2000);
    }
  }
  await sleep(3000);

  const urlNow = page.url();
  if (urlNow.includes(channelId)) {
    console.log('  ✅ 이미 대상 채널');
    return true;
  }
  console.log('  현재 URL:', urlNow.substring(0, 80));

  for (let i = 0; i < 5; i++) {
    const avatarBtn =
      await page.$('#avatar-btn').catch(() => null) ||
      await page.$('button#avatar-btn').catch(() => null) ||
      await page.$('[aria-label*="채널"]').catch(() => null) ||
      await page.$('ytd-topbar-logo-renderer #avatar-btn').catch(() => null);
    if (avatarBtn) {
      console.log('  아바타 버튼 클릭...');
      await avatarBtn.click().catch(() => {});
      await sleep(2000);
      break;
    }
    await sleep(1500);
  }

  const switched = await page.evaluate(() => {
    const els = document.querySelectorAll('button, [role="menuitem"], a');
    for (const el of els) {
      const t = (el.innerText || el.textContent || '').trim();
      if (t === '계정 전환' || t === 'Switch account') { el.click(); return t; }
    }
    return null;
  }).catch(() => null);
  if (switched) {
    console.log(`  "${switched}" 클릭`);
    await sleep(2500);
  }

  const names = [channelSlug, channelHandle];
  const clicked = await page.evaluate((names) => {
    const els = document.querySelectorAll('[role="menuitem"], button, a, yt-formatted-string, #channel-name');
    for (const el of els) {
      const t = (el.innerText || el.textContent || '').trim();
      for (const n of names) {
        if (t.toLowerCase().includes(n.toLowerCase().replace(/^@/, ''))) {
          const clickTarget = el.closest('[role="menuitem"]') || el.closest('button') || el;
          clickTarget.click();
          return t;
        }
      }
    }
    return null;
  }, names).catch(() => null);

  if (clicked) {
    console.log(`  ✅ "${clicked}" 선택`);
    await sleep(5000);
    console.log('  전환 후 URL:', (page.url()).substring(0, 80));
    return true;
  }

  console.log('  UI 전환 실패 → 직접 URL 이동 시도...');
  await page.goto(`https://studio.youtube.com/channel/${channelId}`, {
    waitUntil: 'domcontentloaded', timeout: 30000,
  });
  await sleep(3000);
  console.log('  URL:', (page.url()).substring(0, 80));
  return true;
}

async function startCallbackServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const qs = url.parse(req.url, true).query;
      if (qs.code) {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end('<h1>✅ 인증 완료.</h1>');
        server.close();
        resolve(qs.code);
      } else {
        res.end('waiting...');
      }
    });
    server.listen(3000, '0.0.0.0', () => console.log('  localhost:3000 대기 중...'));
    server.on('error', (e) => { console.log('  포트 오류:', e.message); resolve(null); });
  });
}

(async () => {
  const secret = JSON.parse(fs.readFileSync(SECRET_PATH));
  const { client_id, client_secret } = secret.installed;
  const oauth2 = new google.auth.OAuth2(client_id, client_secret, 'http://localhost:3000/callback');

  const authUrl = oauth2.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    login_hint: accountEmail,
    prompt: 'consent',
  });

  console.log(`\n[${accountId.toUpperCase()}] ${accountEmail} → ${channelHandle}`);

  const codePromise = startCallbackServer();

  console.log('Chrome 실행 중...');
  const profDir = path.join(require('os').homedir(), '.dtslib-youtube-profiles', `account_${accountId}`);
  fs.mkdirSync(profDir, { recursive: true });
  const chromePath = fs.existsSync('/home/dtsli/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome')
    ? '/home/dtsli/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome'
    : undefined;
  const ctx = await chromium.launchPersistentContext(profDir, {
    executablePath: chromePath,
    headless: false,
    viewport: { width: 1280, height: 900 },
    args: ['--no-first-run', '--no-default-browser-check', '--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-gpu', '--disable-software-rasterizer', '--disable-dev-shm-usage', '--disable-quic', '--disable-features=UseDnsHttpsSvcbAlpn'],
    ignoreDefaultArgs: ['--enable-automation', '--disable-infobars'],
    ignoreHTTPSErrors: true,
    timeout: 30000,
  });

  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
    delete window.__playwright;
  });

  const page = await ctx.newPage();

  await switchToChannel(page);

  console.log('\nOAuth URL 이동...');
  for (let i = 0; i < 4; i++) {
    try {
      await page.goto(authUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      break;
    } catch (e) {
      console.log(`  authUrl goto 실패 (시도 ${i + 1}/4): ${e.message.slice(0, 120)}`);
      if (i === 3) throw e;
      await sleep(2000);
    }
  }
  await sleep(2000);
  console.log('페이지:', await page.title());

  // 브랜드 계정 선택 화면(Google)의 실제 표시명은 YouTube 핸들과 다르다
  // (2026-07-06 실측: 채널 chooser에 뜨는 이름은 옛 페르소나 초안명).
  // 확인된 매핑만 기입 — 불확실한 건 넣지 않는다.
  const KNOWN_BRAND_TILE_NAMES = {
    '@musician-parksy': ['작곡가 싼쵸'],
    '@BeingEduartEngineer-4': ['Being Eduart Engineer'],
    // 2026-07-22 실측 — account a 브랜드 타일 chooser에 뜨는 옛 페르소나 초안명.
    // 웹툰작가 디마쓰/프로그래머 톰하스/방송인 박씨는 이름으로 매칭 확인,
    // 사업가 디티스립=philosopher-parksy는 5개 중 나머지 소거법으로 확정
    // (chooser에 정확히 5개 브랜드 타일만 뜨고 이 중 4개는 이름/역할 매칭 확정됨).
    '@visualizer-parksy': ['웹툰작가 디마쓰'],
    '@technician-parksy': ['프로그래머 톰하스'],
    '@방송인박씨-v1o': ['방송인 박씨'],
    '@philosopher-parksy': ['사업가 디티스립'],
  };
  const candidateNames = KNOWN_BRAND_TILE_NAMES[channelHandle] || [];

  // 이 chooser는 /v3/signin/... 과 /oauth/delegation 양쪽 URL에서 똑같이 다시
  // 나타날 수 있다 (2026-07-06 실측 — URL이 delegation이어도 실제로는 같은
  // "계정 또는 브랜드 계정 선택" 화면). 그래서 클릭 함수를 재사용 가능하게 분리하고
  // 루프 안에서도 매번 재시도한다 — 한 번만 시도하고 넘어가지 않는다.
  async function tryClickBrandTile() {
    await page.screenshot({ path: '/tmp/oauth_chooser.png' }).catch(() => {});
    const handles = await page.$$('[data-identifier], div[role="link"], li').catch(() => []);
    const texts = [];
    for (const h of handles) {
      const t = (await h.innerText().catch(() => '')).trim();
      texts.push(t);
    }
    if (texts.filter(Boolean).length) console.log('  [선택지 후보]', JSON.stringify(texts.filter(Boolean).slice(0, 20)));

    // el.click()(JS 합성 이벤트)는 Google 컴포넌트가 무시함(isTrusted=false).
    // 반드시 Playwright의 실제 마우스 클릭(elementHandle.click)을 써야 한다.
    // (2026-07-06 실측 — 합성 클릭으로는 같은 chooser 페이지에서 무한 루프)
    for (let i = 0; i < handles.length; i++) {
      const t = texts[i];
      if (!t || t.length >= 60) continue;
      const isMatch = candidateNames.some(c => t.includes(c)) ||
        t.toLowerCase().includes(channelSlug.toLowerCase()) || t.includes(channelHandle);
      if (isMatch) {
        await handles[i].click({ force: true, timeout: 5000 }).catch(async () => {
          const box = await handles[i].boundingBox().catch(() => null);
          if (box) await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
        });
        return t;
      }
    }
    return null;
  }

  const isChooserPage = async () => {
    const t = await page.innerText('body').catch(() => '');
    return t.includes('계정 또는 브랜드 계정 선택') || t.includes('Choose an account');
  };

  if (await isChooserPage()) {
    const brandTile = await tryClickBrandTile();
    if (brandTile) {
      console.log(`  ✅ 브랜드 계정 타일 매칭 클릭: "${brandTile}"`);
      await sleep(3000);
    } else {
      const acctBtn = await page.$(`[data-email="${accountEmail}"]`).catch(() => null)
        || await page.$(`[data-identifier="${accountEmail}"]`).catch(() => null);
      if (acctBtn) {
        console.log('  ⚠️ 브랜드 계정 타일 매칭 실패 — 이메일 기준으로만 클릭 (틀린 채널일 수 있음)');
        await acctBtn.click();
        await sleep(3000);
      } else {
        // 속성값 대소문자 불일치(Gmail은 소문자로 정규화됨) 대비 — 텍스트 기준
        // 대소문자 무시 매칭으로 재시도.
        const emailLower = accountEmail.toLowerCase();
        const tileHandles = await page.$$('[data-identifier], [data-email], div[role="link"], li').catch(() => []);
        for (const h of tileHandles) {
          const t = (await h.innerText().catch(() => '')).trim();
          if (t.toLowerCase().includes(emailLower)) {
            console.log(`  ✅ 이메일 텍스트 매칭(대소문자 무시) 타일 클릭: "${t.slice(0, 60)}"`);
            await h.click({ force: true }).catch(async () => {
              const box = await h.boundingBox().catch(() => null);
              if (box) await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
            });
            await sleep(3000);
            break;
          }
        }
      }
    }
  }

  const body1 = await page.innerText('body').catch(() => '');
  if (body1.includes('로그인할 수 없음') || body1.includes("can't sign in") || body1.includes('not be secure')) {
    console.log('⚠️ Google이 브라우저 차단. 이메일/비번 직접 입력 시도...');
    const altLink = await page.$('a[href*="accounts.google.com"]').catch(() => null)
      || await page.$('a:has-text("다른 계정")').catch(() => null)
      || await page.$('a:has-text("다른 방법")').catch(() => null);
    if (altLink) { await altLink.click(); await sleep(2000); }
  }

  const body2 = await page.innerText('body').catch(() => '');
  if (body2.includes('이메일') || body2.includes('Email') || body2.includes('email') || body2.includes('Sign in')) {
    const emailInput = await page.$('input[type="email"], input#identifierId');
    const emailVisible = emailInput ? await emailInput.isVisible().catch(() => false) : false;
    if (emailVisible) {
      console.log('이메일 입력...');
      try {
        await emailInput.fill(accountEmail, { timeout: 5000 });
        await page.keyboard.press('Enter');
        await sleep(3000);
      } catch (e) {
        console.log(`  이메일 입력 스킵(이미 지나온 단계로 보임): ${e.message.slice(0, 100)}`);
      }
    } else {
      console.log('  이메일 입력란 없음 — 이미 지나온 단계로 간주, 비밀번호 단계로 진행');
    }
    let pwInput = null;
    for (let i = 0; i < 6; i++) {
      pwInput = await page.$('input[type="password"]').catch(() => null);
      if (pwInput) break;
      await sleep(1500);
    }
    if (pwInput) {
      console.log('비밀번호 입력...');
      {
        await pwInput.fill(PASSWORD);
        await page.keyboard.press('Enter');
        await sleep(5000);
      }
    }
  }

  console.log('Allow 버튼 대기...');
  for (let i = 0; i < 30; i++) {
    const pageText = await page.innerText('body').catch(() => '');
    const btns = await page.$$eval('button', bs => bs.map(b => b.innerText.trim()).filter(t => t)).catch(() => []);
    const currentUrlNow = page.url();
    console.log(`  [${i+1}] URL: ${currentUrlNow.substring(0,80)} | 버튼: ${JSON.stringify(btns)}`);

    if (currentUrlNow.includes('localhost:3000/callback') || currentUrlNow.includes('127.0.0.1:3000/callback')) {
      console.log('  ✅ callback URL 감지 — 루프 종료');
      break;
    }

    if (currentUrlNow.includes('servicerestricted')) {
      console.log('  ⛔ servicerestricted 페이지 감지 — 본문 텍스트 덤프:');
      console.log('  ---');
      console.log('  ' + pageText.replace(/\n/g, '\n  '));
      console.log('  ---');
      await page.screenshot({ path: '/tmp/servicerestricted.png' }).catch(() => {});
      break;
    }

    const finalAllowBtn =
      await page.$('button:has-text("허용")').catch(() => null) ||
      await page.$('button:has-text("Allow")').catch(() => null);
    if (finalAllowBtn) {
      console.log('  ✅ 최종 Allow 버튼 — 클릭!');
      await finalAllowBtn.click();
      await sleep(3000);
      break;
    }

    if (currentUrlNow.includes('/consentsummary')) {
      const denyDialog = await page.$('button:has-text("돌아가기")').catch(() => null);
      if (denyDialog && btns.includes('돌아가기')) {
        console.log('  ⚠️ 거부 다이얼로그 감지 — 돌아가기 클릭');
        await denyDialog.click({ force: true }).catch(() => {});
        await sleep(2000);
      }
      const selectAll = await page.$('input[type="checkbox"]').catch(() => null);
      if (selectAll) {
        const checked = await selectAll.isChecked().catch(() => false);
        if (!checked) {
          console.log('  ☑️ 모두 선택 체크박스 클릭...');
          await selectAll.click({ force: true }).catch(async () => {
            await page.evaluate(() => {
              const cb = document.querySelector('input[type="checkbox"]');
              if (cb) cb.click();
            });
          });
          await sleep(1500);
        }
      }
    }

    // 브랜드 계정 "위임" 확인 페이지 — 버튼 텍스트가 "허용/계속"이 아니라
    // 계정/채널 이름 자체인 경우가 있음 (2026-07-06 실측: 버튼 텍스트 "parksy")
    // "delegation" URL도 실제로는 같은 브랜드 계정 chooser로 되돌아온 것일 수
    // 있음 (2026-07-06 실측 — 스크린샷으로 확인). 버튼을 아무거나 누르는 대신
    // 매번 chooser 감지 함수로 다시 판단한다.
    if (currentUrlNow.includes('/oauth/delegation') || await isChooserPage()) {
      console.log('  🔁 chooser 재등장 감지 — 브랜드 타일 재매칭 시도...');
      const brandTile2 = await tryClickBrandTile();
      if (brandTile2) {
        console.log(`  ✅ 브랜드 계정 타일 재매칭 클릭: "${brandTile2}"`);
        await sleep(3000);
        continue;
      }
      console.log('  ⚠️ 재매칭 실패 — 스크린샷 저장 후 다음 핸들러로');
      await page.screenshot({ path: '/tmp/delegation_no_match.png' }).catch(() => {});
    }

    const currentUrl = page.url();
    if (currentUrl.includes('/signin/oauth/warning') || currentUrl.includes('/oauth/warning')) {
      console.log('  ⚠️ warning 페이지 감지 — 고급 → 계속 2단계 클릭...');
      const advClicked = await page.evaluate(() => {
        const all = document.querySelectorAll('a, button, [role="button"], span');
        for (const el of all) {
          const txt = el.innerText ? el.innerText.trim() : '';
          if (txt === '고급' || txt === 'Advanced' || txt === 'Show Advanced') { el.click(); return true; }
        }
        return false;
      }).catch(() => false);
      if (advClicked) { console.log('  ✅ 고급(Advanced) 클릭'); await sleep(1500); }

      const warnCont =
        await page.$('a:has-text("계속")').catch(() => null) ||
        await page.$('button:has-text("계속")').catch(() => null) ||
        await page.$('[jsname="ozardib"]').catch(() => null) ||
        await page.$('[data-action="proceed"]').catch(() => null);
      if (warnCont) { console.log('  ✅ 계속 클릭'); await warnCont.click(); await sleep(3000); continue; }

      const clicked = await page.evaluate(() => {
        const all = document.querySelectorAll('a, button, [role="button"]');
        for (const el of all) {
          const txt = el.innerText ? el.innerText.trim() : '';
          const href = el.href || '';
          if (txt === '계속' || txt === 'Continue' || txt.includes('안전하지 않음') || txt.includes('이동') ||
              href.includes('proceed') || href.includes('confirm')) { el.click(); return txt || href; }
        }
        return false;
      }).catch(() => false);
      if (clicked) { console.log('  ✅ evaluate() 계속 클릭 성공'); await sleep(3000); continue; }

      console.log('  ❌ 계속 버튼 못 찾음 — 스크린샷+HTML 저장');
      await page.screenshot({ path: '/tmp/warning_page.png' });
      const html = await page.content().catch(() => '');
      fs.writeFileSync('/tmp/warning_page.html', html.substring(0, 50000));
    }

    const contBtns = await page.$$('button:has-text("계속")').catch(() => []);
    const contBtnEN = await page.$$('button:has-text("Continue")').catch(() => []);
    const allContBtns = [...contBtns, ...contBtnEN];
    const contBtn = allContBtns.length > 0 ? allContBtns[0] : await page.$('[jsname="b3VHJd"]').catch(() => null);
    if (contBtn) {
      console.log(`  ➡️ 중간 버튼 클릭 (${allContBtns.length}개 중)...`);
      try { await contBtn.click({ force: true, timeout: 5000 }); }
      catch (e) {
        try {
          const box = await contBtn.boundingBox();
          if (box) await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
        } catch (e2) { console.log('  ❌ 모든 클릭 방법 실패'); }
      }
      await sleep(3000);
      continue;
    }

    if (pageText.includes('2단계 인증') || pageText.includes('2-Step') || pageText.includes('본인 확인')) {
      console.log('  📱 2FA 대기 중 — 핸드폰에서 승인해주세요...');
      await sleep(8000);
      continue;
    }

    if (pageText.includes('비밀번호') || pageText.includes('password') || pageText.includes('Password')) {
      const pwInput = await page.$('input[type="password"]').catch(() => null);
      if (pwInput) {
        console.log('  비밀번호 입력...');
        await pwInput.fill(PASSWORD);
        await page.keyboard.press('Enter');
        await sleep(5000);
        continue;
      }
    }

    const clicked2 = await page.click('#identifierNext, #passwordNext', { timeout: 3000 }).then(() => true).catch(() => false);
    if (clicked2) { await sleep(3000); continue; }

    await sleep(5000);
  }

  console.log('\n인증 코드 대기 중...');
  const code = await Promise.race([codePromise, sleep(120000).then(() => null)]);
  await ctx.close();

  if (!code) {
    console.log('❌ 코드 수신 실패');
    process.exit(1);
  }

  console.log('코드 수신:', code.substring(0, 20) + '...');
  const { tokens } = await oauth2.getToken(code);
  oauth2.setCredentials(tokens);

  fs.mkdirSync(path.dirname(TOKEN_PATH), { recursive: true });
  fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));
  console.log(`\n✅ ${path.basename(TOKEN_PATH)} 저장 완료`);
  console.log('  refresh_token:', tokens.refresh_token ? '있음 ✅' : '없음 ⚠️');

  try {
    const yt = google.youtube({ version: 'v3', auth: oauth2 });
    const res = await yt.channels.list({ part: ['snippet'], mine: true });
    const ch = res.data.items?.[0];
    console.log('✅ 채널:', ch?.snippet?.title || '(채널 없음)', '| id:', ch?.id);
    if (ch?.id !== channelId) {
      console.log(`⚠️ 경고: 요청한 채널(${channelId})과 실제 발급된 채널(${ch?.id})이 다름 — 전환 실패 가능성`);
    }
  } catch (e) {
    console.log('⚠️ YouTube API 검증 실패:', e.message);
  }

  process.exit(0);
})();
