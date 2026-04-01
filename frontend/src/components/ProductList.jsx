import React, { useState, useEffect } from 'react';
import { productService } from '../services/api';

export default function ProductList() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);

  // Filters
  const [filters, setFilters] = useState({
    brand: '',
    category: '',
    source: '',
    min_price: '',
    max_price: '',
    skip: 0,
    limit: 20,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  useEffect(() => {
    loadProducts();
  }, [filters]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const response = await productService.getProducts(filters);
      setProducts(response.data.data);
      setError(null);
    } catch (err) {
      console.error('Error loading products:', err);
      setError('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const handleProductClick = async (product) => {
    setSelectedProduct(product);
    try {
      const response = await productService.getPriceHistory(product.id);
      setPriceHistory(response.data);
    } catch (err) {
      console.error('Error loading price history:', err);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters({
      ...filters,
      [key]: value,
      skip: 0, // Reset pagination on filter change
    });
  };

  const handleResetFilters = () => {
    setFilters({
      brand: '',
      category: '',
      source: '',
      min_price: '',
      max_price: '',
      skip: 0,
      limit: 20,
      sort_by: 'created_at',
      sort_order: 'desc',
    });
  };

  return (
    <div className="bg-gray-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Products</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filters */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Filters</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
                  <input
                    type="text"
                    placeholder="Filter by brand..."
                    value={filters.brand}
                    onChange={(e) => handleFilterChange('brand', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <input
                    type="text"
                    placeholder="Filter by category..."
                    value={filters.category}
                    onChange={(e) => handleFilterChange('category', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
                  <select
                    value={filters.source}
                    onChange={(e) => handleFilterChange('source', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Sources</option>
                    <option value="grailed">Grailed</option>
                    <option value="fashionphile">Fashionphile</option>
                    <option value="1stdibs">1stdibs</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Min Price</label>
                  <input
                    type="number"
                    placeholder="Min price..."
                    value={filters.min_price}
                    onChange={(e) => handleFilterChange('min_price', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Price</label>
                  <input
                    type="number"
                    placeholder="Max price..."
                    value={filters.max_price}
                    onChange={(e) => handleFilterChange('max_price', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
                  <select
                    value={filters.sort_by}
                    onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="created_at">Date Added</option>
                    <option value="price">Price</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Order</label>
                  <select
                    value={filters.sort_order}
                    onChange={(e) => handleFilterChange('sort_order', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="desc">Descending</option>
                    <option value="asc">Ascending</option>
                  </select>
                </div>

                <button
                  onClick={handleResetFilters}
                  className="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
                >
                  Reset Filters
                </button>
              </div>
            </div>
          </div>

          {/* Products List */}
          <div className="lg:col-span-3">
            {loading ? (
              <div className="text-center py-8">Loading products...</div>
            ) : (
              <>
                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-100 border-b">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Product</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Brand</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Price</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Source</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {products.map((product) => (
                          <tr key={product.id} className="border-b hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm text-gray-900">{product.name}</td>
                            <td className="px-6 py-4 text-sm text-gray-700">{product.brand || '-'}</td>
                            <td className="px-6 py-4 text-sm text-gray-900 font-bold">${product.price.toFixed(2)}</td>
                            <td className="px-6 py-4 text-sm text-gray-700 capitalize">{product.source}</td>
                            <td className="px-6 py-4 text-sm">
                              <button
                                onClick={() => handleProductClick(product)}
                                className="text-blue-600 hover:text-blue-800 font-medium"
                              >
                                Details
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Product Details Modal */}
                {selectedProduct && (
                  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-96 overflow-y-auto">
                      <div className="p-6">
                        <div className="flex justify-between items-start mb-4">
                          <h2 className="text-2xl font-bold text-gray-900">{selectedProduct.name}</h2>
                          <button
                            onClick={() => setSelectedProduct(null)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            ✕
                          </button>
                        </div>

                        <div className="mb-4 space-y-2">
                          <p className="text-gray-700"><strong>Brand:</strong> {selectedProduct.brand}</p>
                          <p className="text-gray-700"><strong>Category:</strong> {selectedProduct.category}</p>
                          <p className="text-gray-700"><strong>Source:</strong> {selectedProduct.source}</p>
                          <p className="text-gray-700"><strong>Price:</strong> ${selectedProduct.price.toFixed(2)}</p>
                          <p className="text-gray-700"><strong>Condition:</strong> {selectedProduct.condition || '-'}</p>
                        </div>

                        {selectedProduct.description && (
                          <div className="mb-4">
                            <p className="text-gray-700"><strong>Description:</strong></p>
                            <p className="text-gray-600">{selectedProduct.description}</p>
                          </div>
                        )}

                        {priceHistory.length > 0 && (
                          <div className="mb-4">
                            <h3 className="text-lg font-bold text-gray-900 mb-2">Price History</h3>
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                              {priceHistory.map((entry, idx) => (
                                <div key={idx} className="p-2 bg-gray-50 rounded">
                                  <p className="text-sm text-gray-700">
                                    <strong>${entry.new_price.toFixed(2)}</strong> on {new Date(entry.recorded_at).toLocaleDateString()}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <a
                          href={selectedProduct.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                        >
                          View on Marketplace →
                        </a>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
