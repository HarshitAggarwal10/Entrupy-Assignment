import React, { useState, useEffect } from 'react';
import { productService } from '../services/api';

export default function UsageStats() {
  const [usage, setUsage] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadUsageStats();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadUsageStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadUsageStats = async () => {
    try {
      setRefreshing(true);
      const response = await productService.getUserUsageStats();
      if (response.data) {
        setUsage(response.data);
        setError(null);
      }
    } catch (err) {
      console.error('Error loading usage stats:', err);
      setError('Failed to load usage statistics. Make sure you are logged in.');
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await productService.getUserUsageHistory(0, 15);
      if (response.data && response.data.logs) {
        setHistory(response.data.logs);
      }
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'history' && history.length === 0) {
      loadHistory();
    }
  };

  if (loading && !usage) {
    return (
      <div className="min-h-screen py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center h-40">
            <div className="text-center">
              <p className="text-gray-700">Loading usage statistics...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="border border-red-300 bg-white text-red-700 px-4 py-3">
            ⚠️ {error}
          </div>
        </div>
      </div>
    );
  }

  if (!usage) {
    return (
      <div className="min-h-screen py-8 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-gray-700">No usage data available</p>
        </div>
      </div>
    );
  }

  // Calculate progress percentages
  const dailyPercent = (usage.requests_today / usage.limit_today) * 100;
  const monthlyPercent = (usage.requests_this_month / usage.limit_this_month) * 100;

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">API Usage</h1>
          <button
            onClick={loadUsageStats}
            disabled={refreshing}
            className={`px-4 py-2 text-sm font-normal ${
              refreshing
                ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
            }`}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Summary Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Daily Quota Card */}
          <div className="border border-gray-300 p-4">
            <h2 className="text-sm font-bold text-gray-900 mb-3">Daily Quota</h2>
            <div className="mb-3">
              <div className="flex justify-between text-sm mb-2">
                <span className="font-bold text-gray-900">
                  {usage.requests_today.toLocaleString()}
                </span>
                <span className="text-gray-600">
                  of {usage.limit_today.toLocaleString()}
                </span>
              </div>
            </div>
            <div className="w-full bg-gray-200 h-2 mb-2">
              <div
                className="h-2 bg-blue-600"
                style={{ width: `${Math.min(dailyPercent, 100)}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-600">
              {dailyPercent.toFixed(1)}% used | Remaining: {usage.requests_remaining_today.toLocaleString()}
            </p>
          </div>

          {/* Monthly Quota Card */}
          <div className="border border-gray-300 p-4">
            <h2 className="text-sm font-bold text-gray-900 mb-3">Monthly Quota</h2>
            <div className="mb-3">
              <div className="flex justify-between text-sm mb-2">
                <span className="font-bold text-gray-900">
                  {usage.requests_this_month.toLocaleString()}
                </span>
                <span className="text-gray-600">
                  of {usage.limit_this_month.toLocaleString()}
                </span>
              </div>
            </div>
            <div className="w-full bg-gray-200 h-2 mb-2">
              <div
                className="h-2 bg-green-600"
                style={{ width: `${Math.min(monthlyPercent, 100)}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-600">
              {monthlyPercent.toFixed(1)}% used | Remaining: {usage.requests_remaining_month.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Tabs Section */}
        <div className="border border-gray-300">
          {/* Tab Navigation */}
          <div className="border-b border-gray-300 flex">
            <button
              onClick={() => handleTabChange('summary')}
              className={`flex-1 px-4 py-3 text-sm font-normal border-b-2 ${
                activeTab === 'summary'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-700'
              }`}
            >
              Top Endpoints
            </button>
            <button
              onClick={() => handleTabChange('history')}
              className={`flex-1 px-4 py-3 text-sm font-normal border-b-2 ${
                activeTab === 'history'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-700'
              }`}
            >
              Recent Requests
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-4">
            {/* Top Endpoints Tab */}
            {activeTab === 'summary' && (
              <div>
                <h3 className="text-sm font-bold text-gray-900 mb-4">Top Endpoints</h3>

                {usage.top_endpoints && usage.top_endpoints.length > 0 ? (
                  <div className="space-y-2">
                    {usage.top_endpoints.map((endpoint, idx) => {
                      const endpointPercent =
                        (endpoint.requests / usage.requests_today) * 100;
                      return (
                        <div key={idx} className="p-2 border border-gray-200">
                          <div className="flex justify-between text-xs mb-1">
                            <span className="font-bold text-gray-900">
                              {idx + 1}. {endpoint.endpoint}
                            </span>
                            <span className="text-gray-600">{endpoint.requests} requests</span>
                          </div>
                          <div className="w-full bg-gray-200 h-1">
                            <div
                              className="h-1 bg-blue-600"
                              style={{ width: `${endpointPercent}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">{endpointPercent.toFixed(1)}%</p>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-center py-4 text-gray-500 text-sm">No requests logged yet</p>
                )}
              </div>
            )}

            {/* Recent Requests Tab */}
            {activeTab === 'history' && (
              <div>
                <h3 className="text-sm font-bold text-gray-900 mb-4">Recent Requests</h3>
                {history.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-300">
                          <th className="px-2 py-2 text-left text-xs font-bold text-gray-600">Endpoint</th>
                          <th className="px-2 py-2 text-left text-xs font-bold text-gray-600">Method</th>
                          <th className="px-2 py-2 text-left text-xs font-bold text-gray-600">Status</th>
                          <th className="px-2 py-2 text-right text-xs font-bold text-gray-600">Time (ms)</th>
                          <th className="px-2 py-2 text-right text-xs font-bold text-gray-600">Timestamp</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map((log, idx) => (
                          <tr key={idx} className="border-b border-gray-200">
                            <td className="px-2 py-2 text-xs text-gray-900">{log.endpoint}</td>
                            <td className="px-2 py-2 text-xs text-gray-900">{log.method}</td>
                            <td className="px-2 py-2 text-xs text-gray-900">{log.status}</td>
                            <td className="px-2 py-2 text-xs text-right text-gray-900">{log.response_time_ms.toFixed(2)}</td>
                            <td className="px-2 py-2 text-xs text-right text-gray-600">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-center py-4 text-gray-500 text-sm">Loading...</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Info Box */}
        <div className="mt-6 border border-gray-300 p-3">
          <p className="text-sm text-gray-700">
            Info: Your API usage resets every day at midnight UTC and every month on the 1st at UTC.
          </p>
        </div>
      </div>
    </div>
  );
}
