#!/usr/bin/env node
// Static integrity audit for the built site: duplicate ids, heading order and
// internal links/anchors. Reads dist/ only; exits 1 when anything is wrong.
//
// Usage: node scripts/check-links.mjs [distDir]

import fs from 'node:fs/promises';
import path from 'node:path';

const DIST = path.resolve(process.argv[2] || 'dist');
const EXTERNAL = /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i;
const SKIP_SCHEMES = /^(?:mailto:|tel:|javascript:|data:)/i;

function toPosix(value) {
  return value.split(path.sep).join('/');
}

async function listHtml(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await listHtml(full));
    } else if (entry.isFile() && entry.name.endsWith('.html')) {
      files.push(full);
    }
  }
  return files.sort();
}

function stripRawText(html) {
  return html
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<script\b[\s\S]*?<\/script>/gi, '')
    .replace(/<style\b[\s\S]*?<\/style>/gi, '');
}

function parseTags(text) {
  const tags = [];
  const re = /<([a-zA-Z][\w:-]*)((?:[^>"']|"[^"]*"|'[^']*')*)>/g;
  let match;
  while ((match = re.exec(text)) !== null) {
    const name = match[1].toLowerCase();
    const attrs = {};
    const attrRe = /([:\w-]+)(?:\s*=\s*("([^"]*)"|'([^']*)'|([^\s>"']+)))?/g;
    let attr;
    while ((attr = attrRe.exec(match[2])) !== null) {
      const key = attr[1].toLowerCase();
      if (key in attrs) continue;
      const raw = attr[3] ?? attr[4] ?? attr[5] ?? '';
      attrs[key] = raw.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    }
    tags.push({ name, attrs, index: match.index });
  }
  return tags;
}

function lineAt(newlines, index) {
  let low = 0;
  let high = newlines.length;
  while (low < high) {
    const mid = (low + high) >> 1;
    if (newlines[mid] <= index) low = mid + 1;
    else high = mid;
  }
  return low + 1;
}

function distFileFor(urlPath) {
  const clean = decodeURIComponent(urlPath.split('?')[0].split('#')[0]);
  if (!clean.startsWith('/')) return null;
  let rel = clean.replace(/^\/+/, '');
  if (rel === '' || rel.endsWith('/')) rel += 'index.html';
  else if (!path.extname(rel)) rel = path.join(rel, 'index.html');
  return path.join(DIST, rel);
}

async function exists(file) {
  try {
    const stat = await fs.stat(file);
    return stat.isFile();
  } catch {
    return false;
  }
}

const files = await listHtml(DIST);
const pages = new Map();
const problems = { duplicateIds: [], headingSkips: [], brokenLinks: [], brokenAnchors: [] };

for (const file of files) {
  const html = await fs.readFile(file, 'utf8');
  const pageUrl = '/' + toPosix(path.relative(DIST, file)).replace(/index\.html$/, '');
  const newlines = [];
  for (let i = 0; i < html.length; i += 1) if (html[i] === '\n') newlines.push(i);

  // Duplicate ids are checked against the raw source (comments stripped, scripts
  // kept) so inline widget templates with a re-injected id are caught as well.
  const rawTags = parseTags(html.replace(/<!--[\s\S]*?-->/g, ''));
  const ids = new Map();
  for (const tag of rawTags) {
    if (!tag.attrs.id) continue;
    const entry = ids.get(tag.attrs.id) || [];
    entry.push({ line: lineAt(newlines, tag.index), tag: tag.name });
    ids.set(tag.attrs.id, entry);
  }

  // Heading order and links are checked against rendered markup only.
  const headings = [];
  for (const tag of parseTags(stripRawText(html))) {
    const heading = /^h([1-6])$/.exec(tag.name);
    if (heading) headings.push({ level: Number(heading[1]), line: lineAt(newlines, tag.index) });
  }

  for (const [id, uses] of ids) {
    if (uses.length > 1) {
      problems.duplicateIds.push(`${pageUrl} — id="${id}" ×${uses.length} (lines ${uses.map((u) => u.line).join(', ')})`);
    }
  }

  let previous = 0;
  for (const heading of headings) {
    if (previous && heading.level > previous + 1) {
      problems.headingSkips.push(`${pageUrl}:${heading.line} — h${previous} → h${heading.level}`);
    }
    previous = heading.level;
  }

  pages.set(pageUrl, { ids: new Set(ids.keys()), file });
}

const checkedPages = new Set(['/']);
for (const [pageUrl, data] of pages) {
  checkedPages.add(pageUrl);
  const html = await fs.readFile(data.file, 'utf8');
  const tags = parseTags(stripRawText(html));
  const newlines = [];
  for (let i = 0; i < html.length; i += 1) if (html[i] === '\n') newlines.push(i);

  for (const tag of tags) {
    if (tag.name !== 'a' && tag.name !== 'area') continue;
    const href = (tag.attrs.href || '').trim();
    if (!href || SKIP_SCHEMES.test(href)) continue;
    const line = lineAt(newlines, tag.index);
    if (EXTERNAL.test(href)) continue;

    const [pathPart, hashPart] = href.split('#');
    const targetUrl = pathPart.startsWith('/')
      ? pathPart
      : path.resolve(path.dirname(data.file), pathPart).slice(DIST.length).split(path.sep).join('/') || '/';
    const normalized = targetUrl.endsWith('/') || path.extname(targetUrl)
      ? targetUrl
      : `${targetUrl}/`;
    const cleanUrl = normalized.split('?')[0];
    const targetFile = distFileFor(cleanUrl);

    if (!targetFile || !(await exists(targetFile))) {
      problems.brokenLinks.push(`${pageUrl}:${line} — ${href}`);
      continue;
    }

    if (hashPart) {
      const targetKey = '/' + toPosix(path.relative(DIST, targetFile)).replace(/index\.html$/, '');
      const targetIds = pages.get(targetKey)?.ids;
      if (!targetIds || !targetIds.has(hashPart)) {
        problems.brokenAnchors.push(`${pageUrl}:${line} — ${href}`);
      }
    }
  }
}

const count = Object.values(problems).reduce((sum, list) => sum + list.length, 0);
console.log(`check-links: ${pages.size} pages, ${checkedPages.size} scanned`);
for (const [label, list] of Object.entries(problems)) {
  if (!list.length) continue;
  console.log(`\n${label} (${list.length}):`);
  for (const line of list.slice(0, 100)) console.log(`  ${line}`);
  if (list.length > 100) console.log(`  … ${list.length - 100} more`);
}
if (count > 0) {
  console.log(`\nFAIL — ${count} issue(s)`);
  process.exit(1);
}
console.log('OK — 0 duplicate ids, 0 heading skips, 0 broken links, 0 broken anchors');
