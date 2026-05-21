const express = require('express');
const crypto = require('crypto');
const app = express();

// Keep raw body for signature verification
app.use(express.json({
  verify: (req, res, buf) => {
    req.rawBody = buf;
  }
}));

const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'dev_shared_secret';

function verifySignature(req) {
  const sig = (req.get('x-signature') || '').trim();
  if (!sig) return false;
  const hmac = crypto.createHmac('sha256', WEBHOOK_SECRET).update(req.rawBody || '').digest('hex');
  const expected = `sha256=${hmac}`;
  // Use timing-safe compare
  try {
    const a = Buffer.from(expected);
    const b = Buffer.from(sig);
    if (a.length !== b.length) return false;
    return crypto.timingSafeEqual(a, b);
  } catch (e) {
    return false;
  }
}

// Simple webhook endpoint with HMAC verification
app.post('/webhook', (req, res) => {
  const ok = verifySignature(req);
  if (!ok) {
    console.warn('Webhook signature verification failed for incoming request');
    return res.status(401).json({ error: 'Invalid signature' });
  }

  console.log('Verified webhook received:');
  console.log(JSON.stringify(req.body, null, 2));
  // In real apps: enqueue work, respond quickly
  res.status(200).json({ received: true });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`Webhook server listening on ${PORT}`));
