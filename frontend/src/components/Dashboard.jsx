import React, { useState, useEffect } from 'react';
import { productService } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await productService.getStats();
      setStats(response.data);
      setError(null);
    } catch (err) {
      console.error('Error loading stats:', err);
      setError('Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshData = async () => {
    try {
      setLoading(true);
      await productService.refreshData();
      await loadStats();
      setError(null);
    } catch (err) {
      console.error('Error refreshing data:', err);
      setError('Failed to refresh data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="bg-gray-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <button
            onClick={handleRefreshData}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Refresh Data
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        {stats && (
          <>
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-gray-500 text-sm font-medium">Total Products</h3>
                <p className="text-3xl font-bold text-gray-900">{stats.total_products || 0}</p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-gray-500 text-sm font-medium">Min Price</h3>
                <p className="text-3xl font-bold text-gray-900">
                  ${(stats.price_statistics?.min_price || 0).toFixed(2)}
                </p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-gray-500 text-sm font-medium">Max Price</h3>
                <p className="text-3xl font-bold text-gray-900">
                  ${(stats.price_statistics?.max_price || 0).toFixed(2)}
                </p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-gray-500 text-sm font-medium">Avg Price</h3>
                <p className="text-3xl font-bold text-gray-900">
                  ${(stats.price_statistics?.avg_price || 0).toFixed(2)}
                </p>
              </div>
            </div>

            {/* Products by Source */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Products by Source</h2>
                <div className="space-y-2">
                  {Object.entries(stats.products_by_source || {}).map(([source, count]) => (
                    <div key={source} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-gray-700 font-medium capitalize">{source}</span>
                      <span className="text-gray-900 font-bold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Average Price by Source */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Avg Price by Source</h2>
                <div className="space-y-2">
                  {Object.entries(stats.average_prices_by_source || {}).map(([source, price]) => (
                    <div key={source} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-gray-700 font-medium capitalize">{source}</span>
                      <span className="text-gray-900 font-bold">${price.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Products by Category */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Products by Category</h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {Object.entries(stats.products_by_category || {}).map(([category, count]) => (
                    <div key={category} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-gray-700 font-medium">{category}</span>
                      <span className="text-gray-900 font-bold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Products by Brand */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Top Brands</h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {Object.entries(stats.products_by_brand || {})
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 15)
                    .map(([brand, count]) => (
                      <div key={brand} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <span className="text-gray-700 font-medium">{brand}</span>
                        <span className="text-gray-900 font-bold">{count}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
