/**
 * community.cjs — YouTube 커뮤니티 게시물 작성 v1.0
 *
 * - OAuth 토큰 기반 (auth.cjs로 사전 발급 필요)
 * - community/*.json 스펙 파일 읽기
 * - YouTube Data API v3 (posts.insert)
 *
 * 사용법:
 *   node community.cjs [계정id]           # community/*.json 전체
 *   node community.cjs [계정id] [파일명]  # 특정 파일만
 *
 * 스펙 JSON:
 * {
 *   "account": "b",
 *   "channel_handle": "@dtslib-branch",
 *   "text": "커뮤니티 텍스트",
 *   "image_path": "D:/path/to/image.jpg"  // 선택
 * }
 */

'use strict';

const { google } = require('googleapis');
const fs   = require('fs');
const path = require('path');

const __dir       = __dirname;
const SECRET_PATH = path.join(__dir, 'client_secret.json');
const POSTS_DIR   = path.join(__dir, 'community');

const ACCOUNT_MAP = {
  a: { email: 'dimas.thomas.sancho@gmail.com', token: 'accounts/token_a.json' },
  b: { email: 'dtslib1979@gmail.com',          token: 'accounts/token_b.json' },
  c: { email: 'Thomas.tj.Park@gmail.com',      token: 'accounts/token_c.json' },
  d: { email: 'dimas@dtslib.com',              token: 'accounts/token_d.json' }
};

const accountId  = process.argv[2];
const postFile   = process.argv[3];

if (!accountId || !ACCOUNT_MAP[accountId]) {
  console.log('사용법: node community.cjs [a|b|c|d] [파일명(선택)]');
  process.exit(1);
}

const account    = ACCOUNT_MAP[accountId];
const TOKEN_PATH = path.join(__dir, account.token);

if (!fs.existsSync(TOKEN_PATH)) {
  console.log(`토큰 없음: ${TOKEN_PATH}`);
  console.log(`먼저 실행: node auth.cjs ${accountId}`);
  process.exit(1);
}

fs.mkdirSync(POSTS_DIR, { recursive: true });

let postFiles;
if (postFile) {
  postFiles = [path.join(POSTS_DIR, postFile)];
} else {
  postFiles = fs.readdirSync(POSTS_DIR)
    .filter(f => f.endsWith('.json'))
    .map(f => path.join(POSTS_DIR, f));
}

if (!postFiles.length) {
  console.log('community/ 에 JSON 스펙 파일 없음');
  process.exit(0);
}

// ─── OAuth2 ──────────────────────────────────────────────────
const secret = JSON.parse(fs.readFileSync(SECRET_PATH));
const { client_id, client_secret } = secret.installed;
const oauth2 = new google.auth.OAuth2(client_id, client_secret, 'http://localhost:3000/callback');
const tokens = JSON.parse(fs.readFileSync(TOKEN_PATH));
oauth2.setCredentials(tokens);
oauth2.on('tokens', (newTokens) => {
  fs.writeFileSync(TOKEN_PATH, JSON.stringify({ ...tokens, ...newTokens }, null, 2));
});

// ─── 채널 ID 조회 ─────────────────────────────────────────────
async function getChannelId(yt, handle) {
  const res = await yt.channels.list({
    part: ['id'],
    forHandle: handle.replace('@', '')
  });
  return res.data.items?.[0]?.id || null;
}

// ─── 커뮤니티 포스트 ─────────────────────────────────────────
async function postCommunity(spec) {
  const yt = google.youtube({ version: 'v3', auth: oauth2 });

  let channelId = null;
  if (spec.channel_handle) {
    channelId = await getChannelId(yt, spec.channel_handle);
    if (!channelId) {
      console.log(`  ⚠ 채널 없음: ${spec.channel_handle}`);
      return false;
    }
    console.log(`  채널: ${spec.channel_handle} (${channelId})`);
  }

  // YouTube Community Posts API
  const body = {
    snippet: {
      textOriginal: spec.text,
    }
  };
  if (channelId) body.snippet.channelId = channelId;

  // 이미지 첨부 (있으면)
  if (spec.image_path && fs.existsSync(spec.image_path)) {
    // 이미지는 먼저 YouTube thumbnails/media API로 업로드 후 첨부
    // 현재는 텍스트만 지원 (이미지 업로드는 별도 구현 필요)
    console.log(`  ⚠ 이미지 첨부 미구현 — 텍스트만 게시`);
  }

  const res = await yt.communityPosts.insert({
    part: ['snippet'],
    requestBody: body,
  });

  const postId = res.data.id;
  console.log(`  ✅ 게시 완료: post ID = ${postId}`);
  return postId;
}

// ─── 메인 ──────────────────────────────────────────────────────
(async () => {
  console.log(`=== YouTube 커뮤니티 게시 v1.0 === [${account.email}]`);

  let successCount = 0;
  let failCount    = 0;

  for (const filePath of postFiles) {
    const fileName = path.basename(filePath);
    console.log(`\n${'='.repeat(50)}\n스펙: ${fileName}`);

    let spec;
    try {
      spec = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (e) {
      console.log(`  JSON 파싱 실패: ${e.message}`);
      failCount++;
      continue;
    }

    if (spec.account && spec.account !== accountId) {
      console.log(`  계정 불일치 — 스킵`);
      continue;
    }

    try {
      const postId = await postCommunity(spec);
      if (postId) {
        successCount++;
        const doneDir  = path.join(POSTS_DIR, 'done');
        fs.mkdirSync(doneDir, { recursive: true });
        fs.writeFileSync(
          path.join(doneDir, fileName),
          JSON.stringify({ ...spec, post_id: postId, posted_at: new Date().toISOString() }, null, 2)
        );
        fs.unlinkSync(filePath);
      } else {
        failCount++;
      }
    } catch (e) {
      console.log(`  ❌ 실패: ${e.message}`);
      failCount++;
    }
  }

  console.log(`\n성공: ${successCount}  실패: ${failCount}`);
})();
