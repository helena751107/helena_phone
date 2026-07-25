/**
 * post.cjs — Naver 블로그 포스팅 자동화 v1.0
 *
 * - login.cjs로 추출한 쿠키 사용
 * - SmartEditor One (SE3) contenteditable 방식
 * - posts/*.json 스펙 파일 읽기
 *
 * 사용법:
 *   node post.cjs [계정id]           # posts/*.json 전체 처리
 *   node post.cjs [계정id] [파일명]  # 특정 파일만
 *
 * 예: node post.cjs dtslib
 *     node post.cjs dtslib sample.json
 */

'use strict';

const path = require('path');
const fs   = require('fs');
const { chromium } = require('playwright');

const __dir       = __dirname;
const COOKIES_DIR = path.join(__dir, 'accounts', 'cookies');
const POSTS_DIR   = path.join(__dir, 'posts');
const PROF_BASE   = path.join(process.env.HOME || '/root', '.dtslib-naver-profiles');

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const accountId = process.argv[2];
const postFile  = process.argv[3];

if (!accountId) {
  console.log('사용법: node post.cjs [계정id] [파일명(선택)]');
  process.exit(1);
}

// 크리덴셜에서 naver_id 조회
const CREDS_PATH = path.join(__dir, 'accounts', 'credentials.json');
const creds      = JSON.parse(fs.readFileSync(CREDS_PATH, 'utf8'));
const acc        = creds.accounts.find(a => a.id === accountId);
if (!acc) {
  console.log(`계정 없음: ${accountId}`);
  process.exit(1);
}
const naverId = acc.naver_id;

// 처리할 포스트 파일 목록
let postFiles;
if (postFile) {
  postFiles = [path.join(POSTS_DIR, postFile)];
} else {
  postFiles = fs.readdirSync(POSTS_DIR)
    .filter(f => f.endsWith('.json'))
    .map(f => path.join(POSTS_DIR, f));
}

if (!postFiles.length) {
  console.log(`posts/ 에 JSON 파일 없음`);
  process.exit(1);
}

// ─── 이미지 업로드 ─────────────────────────────────────────
async function uploadImage(page, imagePath) {
  console.log(`  이미지 업로드 시도: ${imagePath}`);
  try {
    // 1. 파일 업로드 input 직접 찾기
    const fileInput = page.locator('input[type="file"]').first();
    if (await fileInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await fileInput.setInputFiles(imagePath);
      console.log('  ✅ input[file] 직접 업로드');
      await sleep(3000);
      return true;
    }

    // 2. filechooser 이벤트 방식 (버튼 클릭 → 파일 선택)
    const fileChooserPromise = page.waitForEvent('filechooser', { timeout: 5000 });
    const imgBtns = [
      'button:has-text("사진")',
      'button:has-text("이미지")',
      '.se-image-toolbar button',
      'button._uploadBtn',
      '[class*="image"] button',
    ];
    let clicked = false;
    for (const sel of imgBtns) {
      try {
        const btn = page.locator(sel).first();
        if (await btn.isVisible({ timeout: 1000 })) {
          await btn.click();
          clicked = true;
          break;
        }
      } catch { /* next */ }
    }
    if (clicked) {
      const fc = await fileChooserPromise;
      await fc.setFiles([imagePath]);
      console.log('  ✅ filechooser 업로드 완료');
      await sleep(3000);
      return true;
    }

    // 3. contenteditable에 <img> 직접 삽입 (외부 URL 또는 base64)
    const imgHtml = `<br><img src="${imagePath}" style="max-width:100%;height:auto;"><br>`;
    const editable = page.locator('[contenteditable="true"]').first();
    if (await editable.isVisible({ timeout: 2000 })) {
      await page.evaluate((html) => {
        const el = document.querySelector('[contenteditable="true"]');
        if (el) {
          el.focus();
          document.execCommand('insertHTML', false, html);
        }
      }, imgHtml);
      console.log('  ✅ contenteditable <img> 직접 삽입');
      return true;
    }
  } catch (e) {
    console.log(`  ⚠ 이미지 업로드 실패: ${e.message}`);
  }
  return false;
}

// ─── SE3 콘텐츠 입력 ───────────────────────────────────────
async function fillSE3Content(page, html) {
  // SE3 에디터 영역 대기
  const editorSel = '.se-component-content, .se-section-editview, [contenteditable="true"]';
  try {
    await page.waitForSelector(editorSel, { timeout: 15000 });
  } catch {
    console.log('  ⚠ SE3 에디터 없음');
    return false;
  }

  // iframe 내부 에디터 시도
  const frames = page.frames();
  for (const frame of frames) {
    try {
      const editable = frame.locator('[contenteditable="true"]').first();
      if (await editable.isVisible({ timeout: 2000 })) {
        await editable.click();
        await sleep(300);
        // 기존 내용 선택 후 교체
        await frame.evaluate((htmlContent) => {
          const el = document.querySelector('[contenteditable="true"]');
          if (el) {
            el.focus();
            document.execCommand('selectAll');
            document.execCommand('insertHTML', false, htmlContent);
          }
        }, html);
        console.log('  ✅ iframe 에디터 입력 완료');
        return true;
      }
    } catch { /* next frame */ }
  }

  // 메인 페이지 contenteditable 시도
  try {
    await page.evaluate((htmlContent) => {
      const el = document.querySelector('.se-component-content [contenteditable="true"], [contenteditable="true"]');
      if (el) {
        el.focus();
        document.execCommand('selectAll');
        document.execCommand('insertHTML', false, htmlContent);
        return true;
      }
      return false;
    }, html);
    console.log('  ✅ 메인 에디터 입력 완료');
    return true;
  } catch (e) {
    console.log(`  ⚠ 에디터 입력 실패: ${e.message}`);
    return false;
  }
}

// ─── 포스트 발행 ────────────────────────────────────────────
async function publishPost(page, post) {
  const writeUrl = `https://blog.naver.com/${naverId}/postwrite`;
  console.log(`  URL: ${writeUrl}`);
  await page.goto(writeUrl, { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(3000);

  // 제목 입력
  const titleSel = '.se-title-input[contenteditable="true"], input[placeholder*="제목"], .blog_title';
  try {
    await page.waitForSelector(titleSel, { timeout: 10000 });
    await page.click(titleSel);
    await sleep(200);
    await page.evaluate((title) => {
      const el = document.querySelector('.se-title-input[contenteditable="true"], input[placeholder*="제목"], .blog_title');
      if (el) {
        if (el.tagName === 'INPUT') {
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
          setter.call(el, title);
          el.dispatchEvent(new Event('input', { bubbles: true }));
        } else {
          el.textContent = title;
          el.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }
    }, post.title);
    console.log(`  제목 입력: ${post.title}`);
  } catch (e) {
    console.log(`  ⚠ 제목 입력 실패: ${e.message}`);
  }
  await sleep(500);

  // 이미지 업로드 (post.images 배열)
  if (post.images && post.images.length) {
    for (const img of post.images) {
      await uploadImage(page, img);
      await sleep(1000);
    }
  }

  // 본문 입력
  const ok = await fillSE3Content(page, post.content);
  if (!ok) {
    console.log('  ❌ 본문 입력 실패 — 포스팅 스킵');
    return false;
  }
  await sleep(500);

  // 태그 입력
  if (post.tags && post.tags.length) {
    try {
      const tagSel = 'input[placeholder*="태그"], .tag_input input, #tag_input';
      const tagEl = page.locator(tagSel).first();
      if (await tagEl.isVisible({ timeout: 3000 })) {
        for (const tag of post.tags) {
          await tagEl.fill(tag);
          await sleep(200);
          await tagEl.press('Enter');
          await sleep(200);
        }
        console.log(`  태그: ${post.tags.join(', ')}`);
      }
    } catch { /* 태그 없으면 스킵 */ }
  }

  // 발행 버튼
  const publishSel = [
    'button:has-text("발행")',
    'button:has-text("공개발행")',
    '.btn_publish',
    '#publish',
  ];
  let published = false;
  for (const sel of publishSel) {
    try {
      const btn = page.locator(sel).first();
      if (await btn.isVisible({ timeout: 3000 })) {
        await btn.click();
        await sleep(2000);
        console.log(`  발행 버튼 클릭 (${sel})`);
        published = true;
        break;
      }
    } catch { /* next */ }
  }
  if (!published) {
    console.log('  ⚠ 발행 버튼 없음');
    return false;
  }

  // 공개 설정 팝업 확인 (있으면 클릭)
  try {
    const confirmBtn = page.locator('button:has-text("공개"), button:has-text("확인"), .btn_confirm').first();
    if (await confirmBtn.isVisible({ timeout: 3000 })) {
      await confirmBtn.click();
      await sleep(2000);
    }
  } catch { /* 팝업 없으면 스킵 */ }

  // 발행 완료 확인
  await sleep(3000);
  const curUrl = page.url();
  if (curUrl.includes('blog.naver.com') && !curUrl.includes('postwrite')) {
    console.log(`  ✅ 발행 완료: ${curUrl}`);
    return true;
  }
  console.log(`  ⚠ 발행 결과 불확실: ${curUrl}`);
  return false;
}

// ─── 메인 ──────────────────────────────────────────────────
(async () => {
  console.log(`=== Naver 블로그 포스팅 v1.0 === [${naverId}]`);

  const profDir   = path.join(PROF_BASE, accountId);
  const statePath = path.join(COOKIES_DIR, `${accountId}_state.json`);

  if (!fs.existsSync(statePath)) {
    console.log(`세션 없음: ${statePath}`);
    console.log('먼저 login.cjs 실행하세요.');
    process.exit(1);
  }

  const browser = await chromium.launch({
    headless: false,
    channel:  'chrome',
    args:     ['--no-sandbox', '--no-first-run', '--no-default-browser-check'],
  });

  const ctx = await browser.newContext({
    viewport:        { width: 1280, height: 900 },
    locale:          'ko-KR',
    storageState:    statePath,
  });

  const page = await ctx.newPage();

  // 로그인 상태 확인
  await page.goto('https://www.naver.com', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await sleep(2000);
  const isLoggedIn = await page.evaluate(() =>
    !!document.querySelector('.gnb_my, .MyView-module__link_avatar, [class*="avatar"]')
  );
  if (!isLoggedIn) {
    console.log('로그인 상태 아님. login.cjs 먼저 실행하세요.');
    await ctx.close();
    process.exit(1);
  }
  console.log('로그인 확인 OK');

  let successCount = 0;
  let failCount    = 0;

  for (const filePath of postFiles) {
    const fileName = path.basename(filePath);
    console.log(`\n${'='.repeat(50)}\n포스트: ${fileName}`);

    let post;
    try {
      post = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (e) {
      console.log(`  JSON 파싱 실패: ${e.message}`);
      failCount++;
      continue;
    }

    // 계정 필터 (post.account가 명시된 경우)
    if (post.account && post.account !== accountId) {
      console.log(`  계정 불일치 (${post.account} ≠ ${accountId}) — 스킵`);
      continue;
    }

    try {
      const ok = await publishPost(page, post);
      if (ok) {
        successCount++;
        // 완료 표시 (파일명에 _done 추가)
        const doneDir  = path.join(POSTS_DIR, 'done');
        fs.mkdirSync(doneDir, { recursive: true });
        fs.renameSync(filePath, path.join(doneDir, fileName));
        console.log(`  파일 이동: posts/done/${fileName}`);
      } else {
        failCount++;
      }
    } catch (e) {
      console.log(`  오류: ${e.message}`);
      failCount++;
    }
    await sleep(3000);
  }

  console.log(`\n${'='.repeat(50)}`);
  console.log(`성공: ${successCount}  실패: ${failCount}`);

  await browser.close();
  console.log('완료');
})();
