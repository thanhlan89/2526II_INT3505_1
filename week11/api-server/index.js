const express = require('express');
const axios = require('axios');
const { EventEmitter } = require('events');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 4100;

// In-memory stores (simple demo)
let items = [];
let nextId = 1;
let webhooks = []; // { id, url }

const bus = new EventEmitter();

// Event-driven handler: deliver events to registered webhooks
bus.on('item.created', async (item) => {
  const payload = { event: 'item.created', timestamp: Date.now(), item };
  for (const wh of webhooks) {
    axios.post(wh.url, payload, { timeout: 5000 })
      .then(res => console.log(`Delivered to ${wh.url}: ${res.status}`))
      .catch(err => console.error(`Deliver failed to ${wh.url}: ${err.message}`));
  }
});

// Helpers
function makeItemLinks(req, item) {
  const base = `${req.protocol}://${req.get('host')}`;
  return {
    self: `${base}/items/${item.id}`,
    update: `${base}/items/${item.id}`,
    delete: `${base}/items/${item.id}`,
    list: `${base}/items`
  };
}

// CRUD + Query
app.get('/items', (req, res) => {
  let results = items.slice();

  // Filtering
  if (req.query.name) {
    const q = req.query.name.toLowerCase();
    results = results.filter(i => i.name.toLowerCase().includes(q));
  }
  if (req.query.minPrice) results = results.filter(i => i.price >= Number(req.query.minPrice));
  if (req.query.maxPrice) results = results.filter(i => i.price <= Number(req.query.maxPrice));

  // Sorting
  if (req.query.sort) {
    const field = req.query.sort;
    const dir = (req.query.order || 'asc') === 'asc' ? 1 : -1;
    results.sort((a,b) => (a[field] > b[field] ? 1 : -1) * dir);
  }

  // Paging
  const page = Math.max(1, Number(req.query.page) || 1);
  const limit = Math.max(1, Number(req.query.limit) || 10);
  const start = (page - 1) * limit;
  const paged = results.slice(start, start + limit);

  // HATEOAS links for collection
  const base = `${req.protocol}://${req.get('host')}`;
  const links = { self: `${base}/items?page=${page}&limit=${limit}` };
  if (start + limit < results.length) links.next = `${base}/items?page=${page+1}&limit=${limit}`;
  if (page > 1) links.prev = `${base}/items?page=${page-1}&limit=${limit}`;

  res.json({ count: results.length, page, limit, links, items: paged.map(i => ({ ...i, links: makeItemLinks(req, i) })) });
});

app.get('/items/:id', (req, res) => {
  const id = Number(req.params.id);
  const item = items.find(i => i.id === id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json({ ...item, links: makeItemLinks(req, item) });
});

app.post('/items', (req, res) => {
  const { name, price } = req.body;
  if (!name || price == null) return res.status(400).json({ error: 'name and price required' });
  const item = { id: nextId++, name, price: Number(price) };
  items.push(item);
  bus.emit('item.created', item);
  res.status(201).location(`/items/${item.id}`).json({ ...item, links: makeItemLinks(req, item) });
});

app.put('/items/:id', (req, res) => {
  const id = Number(req.params.id);
  const item = items.find(i => i.id === id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  const { name, price } = req.body;
  if (name !== undefined) item.name = name;
  if (price !== undefined) item.price = Number(price);
  res.json({ ...item, links: makeItemLinks(req, item) });
});

app.delete('/items/:id', (req, res) => {
  const id = Number(req.params.id);
  const idx = items.findIndex(i => i.id === id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  items.splice(idx, 1);
  res.status(204).end();
});

// Webhook registration endpoints
app.post('/webhooks/register', (req, res) => {
  const { url } = req.body;
  if (!url) return res.status(400).json({ error: 'url required' });
  const wh = { id: webhooks.length + 1, url };
  webhooks.push(wh);
  res.status(201).json(wh);
});

app.get('/webhooks', (req, res) => res.json(webhooks));

app.post('/webhooks/test', async (req, res) => {
  const payload = { event: 'test', timestamp: Date.now(), body: req.body };
  const results = [];
  for (const wh of webhooks) {
    try {
      const r = await axios.post(wh.url, payload, { timeout: 5000 });
      results.push({ id: wh.id, url: wh.url, status: r.status });
    } catch (e) {
      results.push({ id: wh.id, url: wh.url, error: e.message });
    }
  }
  res.json({ results });
});

app.listen(PORT, () => console.log(`API server listening on ${PORT}`));
