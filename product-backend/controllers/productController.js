const Product = require('../models/Product');

async function getProducts(req, res) {
  const products = await Product.find().sort({ createdAt: -1 });
  return res.status(200).json({ products });
}

async function createProduct(req, res) {
  const { name, description, price, inStock, tags } = req.body;
  const product = await Product.create({ name, description, price, inStock, tags });
  return res.status(201).json({ product });
}

async function getProductById(req, res) {
  const { id } = req.params;
  const product = await Product.findById(id);

  if (!product) {
    return res.status(404).json({ error: 'Product not found' });
  }

  return res.status(200).json({ product });
}

async function updateProduct(req, res) {
  const { id } = req.params;
  const updates = req.body;
  const product = await Product.findByIdAndUpdate(id, updates, {
    new: true,
    runValidators: true,
  });

  if (!product) {
    return res.status(404).json({ error: 'Product not found' });
  }

  return res.status(200).json({ product });
}

async function deleteProduct(req, res) {
  const { id } = req.params;
  const product = await Product.findByIdAndDelete(id);

  if (!product) {
    return res.status(404).json({ error: 'Product not found' });
  }

  return res.sendStatus(204);
}

module.exports = {
  getProducts,
  createProduct,
  getProductById,
  updateProduct,
  deleteProduct,
};
