const http = require('http');
const crypto = require('crypto');

const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'dev_shared_secret';

const data = JSON.stringify({
  event: 'order.created',
  timestamp: Date.now(),
  payload: { orderId: 12345, total: 79.9 }
});

const signature = 'sha256=' + crypto.createHmac('sha256', WEBHOOK_SECRET).update(data).digest('hex');

const options = {
  hostname: 'localhost',
  port: 4000,
  path: '/webhook',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(data),
    'x-signature': signature
  }
};

const req = http.request(options, (res) => {
  console.log(`Status: ${res.statusCode}`);
  res.setEncoding('utf8');
  res.on('data', (chunk) => {
    console.log('Response:', chunk);
  });
});

req.on('error', (e) => {
  console.error(`Problem with request: ${e.message}`);
});

req.write(data);
req.end();
