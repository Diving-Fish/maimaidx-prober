const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const config = require('../deploy/config.json');
const release = 'a'.repeat(40) + '-1-1';
const base = config.cdnBase + config.objectPrefix + release + '/';
const local = config.localAssetPrefix + release + '/';
const template = fs.readFileSync(path.join(__dirname, '../public/index.html'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];

function load(assetBase = base, search = '') {
  const events = {}, fontEvents = {}, navigations = [], history = [];
  const window = {addEventListener: (name, fn) => events[name] = fn};
  const location = {origin: 'https://maimai.diving-fish.com', pathname: '/', search, hash: '',
    replace: url => navigations.push(url)};
  const source = template.replace('<%= JSON.stringify(BASE_URL) %>', JSON.stringify(assetBase))
    .replace('<%= JSON.stringify(htmlWebpackPlugin.options.localAssetPrefix) %>', JSON.stringify(config.localAssetPrefix));
  vm.runInNewContext(source, {window, location, URL, URLSearchParams,
    document: {fonts: {addEventListener: (name, fn) => fontEvents[name] = fn}},
    history: {replaceState: (_state, _title, url) => history.push(url)}});
  return {events, fontEvents, navigations, history, window};
}

test('CDN failure selects the same local version, once', () => {
  const state = load();
  state.events.error({target: {src: base + 'js/app.js'}});
  state.events.error({target: {href: base + 'css/app.css'}});
  assert.equal(state.navigations.length, 1);
  assert.equal(state.navigations[0], local + 'index.local.html?__prober_return=%2F');
});

test('unrelated image or application errors do not trigger fallback', () => {
  const state = load();
  state.events.error({target: {src: 'https://other.example/banner.png'}});
  state.events.error({target: {}});
  assert.equal(state.navigations.length, 0);
});

test('font and async chunk failures use the same fallback', () => {
  const font = load();
  font.fontEvents.loadingerror();
  assert.equal(font.navigations.length, 1);
  const chunk = load();
  chunk.events.unhandledrejection({reason: {name: 'ChunkLoadError'}});
  assert.equal(chunk.navigations.length, 1);
});

test('local mode restores the URL and does not install retry listeners', () => {
  const state = load(local, '?__prober_return=%2F%3Fx%3D1');
  assert.equal(state.window.__PROBER_ASSET_BASE__, local);
  assert.deepEqual(state.history, ['https://maimai.diving-fish.com/?x=1']);
  assert.deepEqual(Object.keys(state.events), []);
  assert.deepEqual(Object.keys(state.fontEvents), []);
});

test('local return URL cannot change origin', () => {
  const state = load(local, '?__prober_return=https%3A%2F%2Fevil.example');
  assert.equal(state.history.length, 0);
});

test('ordinary local development does not install CDN fallback', () => {
  const state = load('./');
  assert.deepEqual(Object.keys(state.events), []);
});
