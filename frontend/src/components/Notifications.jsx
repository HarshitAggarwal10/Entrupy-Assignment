import React, { useState, useEffect } from 'react';
import { productService } from '../services/api';

export default function Notifications({ onProcessNotifications = () => {} }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, unprocessed, processed

  useEffect(() => {
    loadNotifications();
  }, [filter]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const is_processed = filter === 'all' ? undefined : filter === 'processed';
      const response = await productService.getNotifications({
        is_processed,
        limit: 100,
      });
      setNotifications(response.data.data);
      setError(null);
    } catch (err) {
      console.error('Error loading notifications:', err);
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessNotifications = async () => {
    try {
      setLoading(true);
      await productService.processNotifications();
      await loadNotifications();
      onProcessNotifications(); // Notify parent to update badge count
      setError(null);
    } catch (err) {
      console.error('Error processing notifications:', err);
      setError('Failed to process notifications');
    } finally {
      setLoading(false);
    }
  };

  const getEventTypeColor = (eventType) => {
    switch (eventType) {
      case 'price_drop':
        return 'bg-green-100 text-green-800';
      case 'price_increase':
        return 'bg-red-100 text-red-800';
      case 'new_product':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getEventTypeLabel = (eventType) => {
    switch (eventType) {
      case 'price_drop':
        return '📉 Price Drop';
      case 'price_increase':
        return 'Price Increase';
      case 'new_product':
        return 'New Product';
      default:
        return eventType;
    }
  };

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex justify-between items-start gap-4">
          <h1 className="text-2xl font-bold">Price Change Notifications</h1>
          <button
            onClick={handleProcessNotifications}
            className="bg-blue-600 text-white font-bold py-2 px-4"
          >
            Process Notifications
          </button>
        </div>

        {error && (
          <div className="bg-red-100 text-red-700 px-4 py-3 mb-4">
            {error}
          </div>
        )}

        {/* Filter Tabs */}
        <div className="mb-6 flex gap-2">
          {['all', 'unprocessed', 'processed'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 font-medium ${
                filter === f
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-8">Loading notifications...</div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-8 bg-white">
            <p className="text-gray-500">No notifications found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className="bg-white p-6 border border-gray-300"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-3 py-1 text-sm font-medium ${getEventTypeColor(notification.event_type)}`}>
                        {getEventTypeLabel(notification.event_type)}
                      </span>
                      {notification.is_processed && (
                        <span className="px-3 py-1 text-sm font-medium bg-gray-100 text-gray-800">
                          ✓ Processed
                        </span>
                      )}
                    </div>

                    <h3 className="text-lg font-bold mb-2">Price Change Detected</h3>

                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div>
                        <p className="text-sm text-gray-600">Old Price</p>
                        <p className="text-xl font-bold">
                          {notification.old_price ? `$${notification.old_price.toFixed(2)}` : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">New Price</p>
                        <p className="text-xl font-bold">
                          ${notification.new_price.toFixed(2)}
                        </p>
                      </div>
                    </div>

                    {notification.change_percentage && (
                      <div>
                        <p className="text-sm text-gray-600">Change</p>
                        <p className={`text-lg font-bold ${
                          notification.change_percentage < 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {notification.change_percentage > 0 ? '↑' : '↓'} {Math.abs(notification.change_percentage).toFixed(2)}%
                        </p>
                      </div>
                    )}

                    <div className="mt-3 pt-3 border-t text-xs text-gray-500">
                      <p>Created: {new Date(notification.created_at).toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="ml-4 text-right">
                    <p className="text-xs text-gray-500 mb-2">Notification ID</p>
                    <p className="text-xs text-gray-700 font-mono">{notification.id}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
