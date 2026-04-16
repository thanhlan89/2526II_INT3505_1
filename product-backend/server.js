const path = require('path');
const fs = require('fs');
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const yaml = require('js-yaml');
const swaggerUI = require('swagger-ui-express');
const { OpenApiValidator } = require('express-openapi-validator');
require('dotenv').config();

const productRoutes = require('./routes/productRoutes');

const app = express();
const port = process.env.PORT || 3000;
const mongoUri = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/product-backend';
const apiSpecPath = path.join(__dirname, 'openapi.yaml');

async function startServer() {
  try {
    await mongoose.connect(mongoUri, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    console.log('Connected to MongoDB:', mongoUri);
  } catch (error) {
    console.error('MongoDB connection failed:', error.message);
    process.exit(1);
  }

  app.use(cors());
  app.use(express.json());

  const openApiDocument = yaml.load(fs.readFileSync(apiSpecPath, 'utf8'));
  app.use('/api-docs', swaggerUI.serve, swaggerUI.setup(openApiDocument));

  app.use(
    OpenApiValidator.middleware({
      apiSpec: apiSpecPath,
      validateRequests: true,
      validateResponses: true,
    })
  );

  app.use('/products', productRoutes);

  app.use((err, req, res, next) => {
    if (err.status && err.errors) {
      return res.status(err.status).json({ error: err.message, details: err.errors });
    }
    console.error(err);
    return res.status(500).json({ error: 'Internal Server Error' });
  });

  app.listen(port, () => {
    console.log(`Product API listening on http://localhost:${port}`);
    console.log(`Swagger UI available at http://localhost:${port}/api-docs`);
  });
}

startServer();
