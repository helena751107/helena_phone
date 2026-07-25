const { chromium } = require('playwright');
const path = require('path');

const WIN_CHROME = '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe';
const WIN_PROFILE = '/mnt/c/Users/dtsli/AppData/Local/Google/Chrome/User Data';

(async () => {
  const ctx = await chromium.launchPersistentContext(WIN_PROFILE, {
    executablePath: WIN_CHROME,
    headless: false,
    viewport: { width: 1280, height: 900 },
    args: [
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-blink-features=AutomationControlled',
      '--profile-directory=Profile 4',
    ],
    ignoreDefaultArgs: ['--enable-automation'],
    timeout: 30000,
  });

  const page = await ctx.newPage();
  await page.goto('https://www.youtube.com/@phoneparis-r6q/playlists', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(4000);
  await page.screenshot({ path: '/tmp/phoneparis_playlists.png', fullPage: false });
  console.log('스크린샷: /tmp/phoneparis_playlists.png');
  
  // 영상 탭도
  await page.goto('https://www.youtube.com/@phoneparis-r6q/videos', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/tmp/phoneparis_videos.png', fullPage: false });
  console.log('스크린샷: /tmp/phoneparis_videos.png');
  
  await ctx.close();
})();
