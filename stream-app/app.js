let entities = [];
let origin = '';
let request = 0;
const $ = selector => document.querySelector(selector);
const timestamp = entity => {
  for (const field of ['_updated', '_created']) {
    const value = Date.parse(entity[field]);
    if (Number.isFinite(value)) return value;
  }
  return -Infinity;
};
const body = (entity, target) => {
  const paragraph = document.createElement('p');
  paragraph.textContent = entity._body || '';
  target.append(paragraph);
};
// Add a renderer for each operational type. Treat all entity values as untrusted text.
const templates = {
  note: body,
  journal(entity, target) {
    body(entity, target);
    if (entity.mood) {
      const mood = document.createElement('small');
      mood.textContent = `Mood · ${entity.mood}`;
      target.append(mood);
    }
  }
};
function parse(text) {
  const ids = new Set();
  return text.split(/\r?\n/).filter(line => line.trim()).map((line, index) => {
    const entity = JSON.parse(line);
    const scalar = value => value === null || ['string', 'number', 'boolean'].includes(typeof value);
    if (!entity || Array.isArray(entity) || typeof entity._id !== 'string' || !entity._id.trim() || /[@.]/.test(entity._id) || ids.has(entity._id) || !Object.values(entity).every(value => scalar(value) || Array.isArray(value) && value.every(scalar))) {
      throw new Error(`Invalid or duplicate entity on record ${index + 1}`);
    }
    ids.add(entity._id);
    return entity;
  });
}
function install(text, description) {
  const next = parse(text);
  entities = next.sort((a, b) => timestamp(b) - timestamp(a) || a._id.localeCompare(b._id));
  origin = description;
  $('#type').replaceChildren(new Option('All types', ''));
  [...new Set(entities.map(entity => String(entity._type || 'entity')))].sort().forEach(type => $('#type').add(new Option(type, type)));
  render();
}
function render() {
  const query = $('#search').value.toLowerCase();
  const type = $('#type').value;
  const shown = entities.filter(entity => (!type || String(entity._type || 'entity') === type) && JSON.stringify(entity).toLowerCase().includes(query));
  const fragment = document.createDocumentFragment();
  for (const entity of shown) {
    const card = $('#card').content.cloneNode(true);
    card.querySelector('.kind').textContent = entity._type || 'entity';
    const time = timestamp(entity);
    card.querySelector('time').textContent = Number.isFinite(time) ? new Date(time).toLocaleString() : 'Undated';
    if (Number.isFinite(time)) card.querySelector('time').dateTime = new Date(time).toISOString();
    card.querySelector('h2').textContent = entity._name || entity._id;
    (Object.hasOwn(templates, entity._type) ? templates[entity._type] : body)(entity, card.querySelector('.content'));
    card.querySelector('pre').textContent = JSON.stringify(entity, null, 2);
    fragment.append(card);
  }
  $('#feed').replaceChildren(fragment);
  $('#status').textContent = `${shown.length} of ${entities.length} signals · ${origin}${shown.length ? '' : ' · No matching signals'}`;
}
async function refresh() {
  const token = ++request;
  $('#status').textContent = 'Reading hub snapshot…';
  try {
    const manifestURL = new URL('../data/manifest.json', location.href);
    const response = await fetch(manifestURL, {cache: 'no-store'});
    if (!response.ok) throw new Error('No hub snapshot yet. Run the collector or open a JSONL file.');
    const manifest = await response.json();
    if (!/^snapshots\/[a-f0-9]{64}\/entities\.jsonl$/.test(manifest.entities)) throw new Error('Invalid snapshot path');
    const snapshot = await fetch(new URL(manifest.entities, manifestURL), {cache: 'no-store'});
    if (!snapshot.ok) throw new Error('Snapshot could not be read');
    const text = await snapshot.text();
    if (token === request) install(text, `Hub collected ${manifest.collected_at}`);
  } catch (error) { if (token === request) $('#status').textContent = `${error.message} Existing feed retained.`; }
}
$('#search').addEventListener('input', render);
$('#type').addEventListener('change', render);
$('#refresh').addEventListener('click', refresh);
$('#file').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  const token = ++request;
  try { const text = await file.text(); if (token === request) install(text, file.name); }
  catch (error) { if (token === request) $('#status').textContent = `${error.message}. Existing feed retained.`; }
});
if ('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch(() => {});
refresh();
