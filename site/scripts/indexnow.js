'use strict';

// IndexNow submission for IndexNow.org (Yandex, Bing, Seznam and others).
// The key is public by design: it is served as /<key>.txt from dist/. The script
// sends every sitemap URL after a deploy; the site is small and deploys are rare,
// so a full batch keeps the logic simple and idempotent.
//
// Usage:
//   node scripts/indexnow.js            # submit dist/sitemap.xml URLs
//   node scripts/indexnow.js --dry-run  # print the payload, send nothing
//   INDEXNOW_DISABLED=1 node ...        # no-op (used by tests / offline builds)

const fs = require('fs');
const path = require('path');

const SITE_DIR = path.join(__dirname, '..');
const DIST = path.join(SITE_DIR, 'dist');
const KEY_FILE = path.join(SITE_DIR, 'src', 'indexnow-key.txt');
const SITE_URL = 'https://antimanager.pro';
const ENDPOINT = 'https://api.indexnow.org/indexnow';

function fail(message) {
  console.error('IndexNow: ' + message);
  process.exit(1);
}

function readSitemapUrls() {
  const sitemapPath = path.join(DIST, 'sitemap.xml');
  if (!fs.existsSync(sitemapPath)) fail('dist/sitemap.xml is missing — run the build first');
  const sitemap = fs.readFileSync(sitemapPath, 'utf-8');
  const urls = [];
  const re = /<loc>([^<]+)<\/loc>/g;
  let match;
  while ((match = re.exec(sitemap)) !== null) {
    if (match[1].indexOf(SITE_URL + '/') === 0) urls.push(match[1]);
  }
  if (!urls.length) fail('sitemap has no ' + SITE_URL + ' URLs');
  return urls;
}

async function main() {
  if (process.env.INDEXNOW_DISABLED === '1') {
    console.log('IndexNow: disabled by INDEXNOW_DISABLED=1');
    return;
  }

  const key = fs.readFileSync(KEY_FILE, 'utf-8').trim();
  if (!/^[a-f0-9]{32}$/.test(key)) fail('src/indexnow-key.txt must hold 32 lowercase hex characters');

  // Guard against a stale key file: the build writes <key>.txt next to the sitemap.
  if (!fs.existsSync(path.join(DIST, key + '.txt'))) {
    fail('dist/' + key + '.txt is missing — run the build so the key file ships');
  }

  const urlList = readSitemapUrls();
  const payload = {
    host: new URL(SITE_URL).host,
    key: key,
    keyLocation: SITE_URL + '/' + key + '.txt',
    urlList: urlList,
  };

  if (process.argv.includes('--dry-run')) {
    console.log('IndexNow (dry run): ' + urlList.length + ' URLs');
    return;
  }

  const response = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(payload),
  });

  // 200/202 mean the batch was accepted; 422 usually means key validation failed.
  if (response.status === 200 || response.status === 202) {
    console.log('IndexNow: submitted ' + urlList.length + ' URLs (HTTP ' + response.status + ')');
    return;
  }

  const body = await response.text().catch(function() { return ''; });
  fail('HTTP ' + response.status + (body ? ' — ' + body.slice(0, 300) : ''));
}

main().catch(function(error) {
  fail(error && error.message ? error.message : String(error));
});
