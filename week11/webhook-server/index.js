const express = require('express');
const app = express();

app.use(express.json());

// Simple webhook endpoint
app.post('/webhook', (req, res) => {
  console.log('Received webhook:');
  console.log(JSON.stringify(req.body, null, 2));
  // In real apps: verify signature, enqueue work, respond quickly
  res.status(200).json({ received: true });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`Webhook server listening on ${PORT}`));
