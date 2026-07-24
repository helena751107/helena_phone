#!/usr/bin/env node
/**
 * sync.cjs — YouTube 채널 설정 자동화 엔진
 *
 * 사용법:
 *   node sync.cjs --config phoneparis/youtube-setup.json [--dry-run]
 *   node sync.cjs --config artrew/youtube-setup.json
 *
 * 동작:
 *   1. channels.json에서 repo명으로 channel_id + account 조회
 *   2. youtube-setup.json 읽어서 API 호출
 *      - channels.update (description, keywords, language, country)
 *      - playlists.insert × N
 *      - channelSections.insert × N
 *   3. run summary + quota 소모 출력
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');

// ── quota 비용표 (YouTube Data API v3) ───────────────────────────
const QUOTA = {
  'channels.update':       50,
  'channels.list':          1,
  'playlists.list':         1,
  'playlists.insert':      50,
  'channelSections.list':   1,
  'channelSections.insert': 50,
};
const DAILY_LIMIT = 60_000;

// ── args ─────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const configFlag = args.indexOf('--config');
const dryRun = args.includes('--dry-run');

if (configFlag === -1 || !args[configFlag + 1]) {
  console.error('Usage: node sync.cjs --config <path/to/youtube-setup.json> [--dry-run]');
  process.exit(1);
}

const configPath = path.resolve(process.env.HOME, args[configFlag + 1]);
const setup = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// ── resolve channel info from channels.json ───────────────────────
const CHANNELS_JSON = path.resolve(__dirname, 'accounts/channels.json');
const channelsRegistry = JSON.parse(fs.readFileSync(CHANNELS_JSON, 'utf8'));

const repoName = path.dirname(args[configFlag + 1]).split('/').pop();

let channelId = null;
let accountId = null;

// _channel_id_ref가 있으면 우선 사용 (다중채널 레포 지원)
if (setup._channel_id_ref) {
  channelId = setup._channel_id_ref;
  accountId = setup._account;
} else {
  for (const account of channelsRegistry.accounts) {
    const ch = account.channels.find(c => c.repo === repoName);
    if (ch) {
      channelId = ch.channel_id;
      accountId = account.id;
      break;
    }
  }
}

if (!channelId) {
  console.error(`❌ channels.json에서 repo="${repoName}" 에 매핑된 채널을 찾을 수 없습니다.`);
  process.exit(1);
}

console.log(`\n▶ Repo: ${repoName}`);
console.log(`▶ Channel ID: ${channelId}`);
console.log(`▶ Account: ${accountId}`);
console.log(`▶ Dry-run: ${dryRun}\n`);

// ── load OAuth token ──────────────────────────────────────────────
const accountEntry = channelsRegistry.accounts.find(a => a.id === accountId);
const tokenPath = path.resolve(__dirname, accountEntry.token_file);
const tokenData = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));
const clientSecret = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'client_secret.json'), 'utf8'));

const { client_id, client_secret } = clientSecret.installed;
const oauth2 = new google.auth.OAuth2(client_id, client_secret);
oauth2.setCredentials(tokenData);

oauth2.on('tokens', (tokens) => {
  const merged = { ...tokenData, ...tokens };
  if (!merged.refresh_token && tokenData.refresh_token) {
    merged.refresh_token = tokenData.refresh_token;
  }
  fs.writeFileSync(tokenPath, JSON.stringify(merged, null, 2));
});

const youtube = google.youtube({ version: 'v3', auth: oauth2 });

// ── run state ────────────────────────────────────────────────────
let quotaUsed = 0;
const runLog = {
  branding: null,   // 'ok' | 'fail' | 'dry'
  playlists: [],    // { title, status: 'created'|'reused'|'failed' }
  sections:  [],    // { title, status: 'created'|'reused'|'skipped'|'failed' }
};

function addQuota(op, count = 1) {
  const cost = (QUOTA[op] || 0) * count;
  quotaUsed += cost;
  return cost;
}

// ── helpers ───────────────────────────────────────────────────────
async function apiCall(label, quotaOp, fn) {
  addQuota(quotaOp);
  if (dryRun) {
    console.log(`[DRY-RUN] ${label}`);
    return { data: { id: `dry-${label}` } };
  }
  try {
    const res = await fn();
    console.log(`✅ ${label}`);
    return res;
  } catch (err) {
    const msg = err?.errors?.[0]?.message || err.message;
    console.error(`❌ ${label}: ${msg}`);
    return null;
  }
}

// ── run summary 출력 ──────────────────────────────────────────────
function printSummary() {
  const plCreated  = runLog.playlists.filter(p => p.status === 'created').length;
  const plReused   = runLog.playlists.filter(p => p.status === 'reused').length;
  const plFailed   = runLog.playlists.filter(p => p.status === 'failed').length;
  const secCreated = runLog.sections.filter(s => s.status === 'created').length;
  const secReused  = runLog.sections.filter(s => s.status === 'reused').length;
  const secSkipped = runLog.sections.filter(s => s.status === 'skipped').length;
  const secFailed  = runLog.sections.filter(s => s.status === 'failed').length;

  const plSummary  = [
    plReused  ? `⏭×${plReused}`   : '',
    plCreated ? `✅×${plCreated}` : '',
    plFailed  ? `❌×${plFailed}`  : '',
  ].filter(Boolean).join(' ') || '—';

  const secSummary = [
    secReused   ? `⏭×${secReused}`   : '',
    secCreated  ? `✅×${secCreated}` : '',
    secSkipped  ? `⚠×${secSkipped}` : '',
    secFailed   ? `❌×${secFailed}`  : '',
  ].filter(Boolean).join(' ') || '—';

  const brandingIcon = runLog.branding === 'ok' ? '✅'
    : runLog.branding === 'fail' ? '❌'
    : runLog.branding === 'dry'  ? '[D]' : '—';

  const pct = ((quotaUsed / DAILY_LIMIT) * 100).toFixed(2);
  const ts  = new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' });

  console.log('\n' + '─'.repeat(60));
  console.log(`  sync run summary    ${ts}`);
  console.log('─'.repeat(60));
  console.log(`  채널    : ${repoName} (${channelId})`);
  console.log(`  계정    : ${accountId}`);
  console.log(`  브랜딩  : ${brandingIcon}`);
  console.log(`  플리    : ${plSummary}`);
  console.log(`  섹션    : ${secSummary}`);
  console.log('─'.repeat(60));
  console.log(`  쿼터 소모: ${quotaUsed.toLocaleString()} units  (계정 ${accountId} 일일 한도 ${DAILY_LIMIT.toLocaleString()} 중 ${pct}%)`);
  console.log('─'.repeat(60) + '\n');
}

// ── main ──────────────────────────────────────────────────────────
(async () => {
  const { channel } = setup;

  // 1. channels.update — brandingSettings
  // NOTE: snippet part not supported (ERROR_PART_UNEXPECTED). description → brandingSettings.
  const brandRes = await apiCall('channels.update (brandingSettings)', 'channels.update', () =>
    youtube.channels.update({
      part: 'brandingSettings',
      requestBody: {
        id: channelId,
        brandingSettings: {
          channel: {
            description: channel.description,
            keywords: channel.keywords.join(' '),
            country: channel.country,
          }
        }
      }
    })
  );
  runLog.branding = dryRun ? 'dry' : (brandRes ? 'ok' : 'fail');

  // 2. playlists — idempotent: reuse by title (mine:true — all go to default channel)
  addQuota('playlists.list');
  const existingPlaylists = dryRun ? { data: { items: [] } }
    : await youtube.playlists.list({ part: 'snippet', mine: true, maxResults: 50 });

  const existingByTitle = {};
  for (const p of (existingPlaylists?.data?.items || [])) {
    existingByTitle[p.snippet.title] = p.id;
  }

  const playlistIds = {};
  for (const pl of setup.playlists) {
    if (existingByTitle[pl.title]) {
      playlistIds[pl.id_key] = existingByTitle[pl.title];
      console.log(`⏭ playlists.reuse "${pl.title}" → ${existingByTitle[pl.title]}`);
      runLog.playlists.push({ title: pl.title, status: 'reused' });
      continue;
    }
    const res = await apiCall(`playlists.insert "${pl.title}"`, 'playlists.insert', () =>
      youtube.playlists.insert({
        part: 'snippet,status',
        requestBody: {
          snippet: {
            title: pl.title,
            description: pl.description,
            tags: pl.tags,
            defaultLanguage: channel.language,
          },
          status: { privacyStatus: pl.privacyStatus }
        }
      })
    );
    if (res?.data?.id) {
      playlistIds[pl.id_key] = res.data.id;
      console.log(`   → playlist_id: ${res.data.id}`);
      runLog.playlists.push({ title: pl.title, status: 'created' });
    } else {
      runLog.playlists.push({ title: pl.title, status: dryRun ? 'reused' : 'failed' });
    }
  }

  // 3. channelSections — idempotent
  // NOTE: insert always targets the account's DEFAULT channel (not target channelId).
  // Dedup by querying the default channel's sections.
  addQuota('channels.list');
  const defaultChannelRes = dryRun ? { data: { items: [{ id: channelId }] } }
    : await youtube.channels.list({ part: 'snippet', mine: true, maxResults: 1 });
  const defaultChannelId = defaultChannelRes?.data?.items?.[0]?.id || channelId;

  addQuota('channelSections.list');
  const existingSectionsRes = dryRun ? { data: { items: [] } }
    : await youtube.channelSections.list({ part: 'snippet', channelId: defaultChannelId });

  const existingSectionTitles = new Set(
    (existingSectionsRes?.data?.items || []).map(s => s.snippet.title)
  );
  const existingCount = existingSectionsRes?.data?.items?.length || 0;
  const remaining = 10 - existingCount;

  if (!dryRun && remaining <= 0) {
    console.warn(`⚠ channelSections 10개 한도 초과 — 섹션 추가 스킵`);
  }

  let sectionCount = 0;
  for (const sec of setup.channelSections) {
    if (existingSectionTitles.has(sec.title)) {
      console.log(`⏭ channelSections.reuse "${sec.title}"`);
      runLog.sections.push({ title: sec.title, status: 'reused' });
      continue;
    }
    if (!dryRun && sectionCount >= remaining) {
      console.warn(`⚠ section "${sec.title}": 한도 도달 — 스킵`);
      runLog.sections.push({ title: sec.title, status: 'skipped' });
      continue;
    }
    sectionCount++;
    const plId = playlistIds[sec.playlist_key];
    if (!plId && !dryRun) {
      console.warn(`⚠ section "${sec.title}": playlist_key=${sec.playlist_key} 없음 — 스킵`);
      runLog.sections.push({ title: sec.title, status: 'skipped' });
      continue;
    }
    const secRes = await apiCall(`channelSections.insert "${sec.title}"`, 'channelSections.insert', () =>
      youtube.channelSections.insert({
        part: 'snippet,contentDetails',
        requestBody: {
          snippet: {
            type: sec.type,
            title: sec.title,
            channelId,
            position: sec.position,
          },
          contentDetails: {
            playlists: [plId || `dry-${sec.playlist_key}`]
          }
        }
      })
    );
    runLog.sections.push({ title: sec.title, status: dryRun ? 'created' : (secRes ? 'created' : 'failed') });
  }

  // 4. save playlist_ids
  if (!dryRun && Object.keys(playlistIds).length > 0) {
    setup._playlist_ids = playlistIds;
    fs.writeFileSync(configPath, JSON.stringify(setup, null, 2));
    console.log('\n💾 playlist_ids → youtube-setup.json에 저장됨');
  }

  printSummary();
})();
