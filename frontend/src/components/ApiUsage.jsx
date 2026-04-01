import React, { useState, useEffect } from 'react';

export default function ApiUsage() {
  const [usage, setUsage] = useState(null);
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('stats');

  useEffect(() => {
    loadUsageData();
  }, []);

  const loadUsageData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const user = JSON.parse(localStorage.getItem('user'));

      // Get usage stats
      const response = await fetch('http://localhost:8000/api/auth/usage', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUsage(data);
        setError(null);
      } else {
        setError('Failed to load usage data');
      }

      // Get usage history
      const historyResponse = await fetch('http://localhost:8000/api/auth/usage/history?limit=20', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setHistory(historyData);
      }
    } catch (err) {
      setError('Error loading usage data');
      console.error(err);
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">API Usage & Limits</h1>
          <p className="text-gray-600 mt-2">Monitor your API usage and remaining quota</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('stats')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              activeTab === 'stats'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Usage Statistics
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              activeTab === 'history'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Request History
          </button>
        </div>

        {/* Stats Tab */}
        {activeTab === 'stats' && usage && (
          <div className="space-y-6">
            {/* Daily Quota */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Daily API Requests</h2>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700 font-medium">
                    {usage.requests_today} / {usage.limit_today} requests
                  </span>
                  <span className="text-gray-500 text-sm">
                    {Math.round((usage.requests_today / usage.limit_today) * 100)}% used
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all"
                    style={{ width: `${Math.min((usage.requests_today / usage.limit_today) * 100, 100)}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-sm text-gray-600 mt-2">
                  <span>Requests remaining today: {usage.requests_remaining_today}</span>
                  <span>Resets at midnight UTC</span>
                </div>
              </div>
            </div>

            {/* Monthly Quota */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Monthly API Requests</h2>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700 font-medium">
                    {usage.requests_this_month} / {usage.limit_this_month} requests
                  </span>
                  <span className="text-gray-500 text-sm">
                    {Math.round((usage.requests_this_month / usage.limit_this_month) * 100)}% used
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      (usage.requests_this_month / usage.limit_this_month) * 100 > 80
                        ? 'bg-red-600'
                        : 'bg-green-600'
                    }`}
                    style={{ width: `${Math.min((usage.requests_this_month / usage.limit_this_month) * 100, 100)}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-sm text-gray-600 mt-2">
                  <span>Requests remaining: {usage.requests_remaining_month}</span>
                  <span>Resets on 1st of month</span>
                </div>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-gray-600 text-sm font-medium mb-2">Total Requests</h3>
                <p className="text-3xl font-bold text-gray-900">{usage.total_requests}</p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-gray-600 text-sm font-medium mb-2">Avg Response Time</h3>
                <p className="text-3xl font-bold text-gray-900">{usage.average_response_time_ms.toFixed(2)}ms</p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-gray-600 text-sm font-medium mb-2">Last Request</h3>
                <p className="text-gray-900">
                  {usage.last_request_timestamp
                    ? new Date(usage.last_request_timestamp).toLocaleString()
                    : 'No requests yet'}
                </p>
              </div>
            </div>

            {/* Top Endpoints */}
            {usage.top_endpoints && usage.top_endpoints.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Most Used Endpoints</h2>
                <div className="space-y-3">
                  {usage.top_endpoints.map((endpoint, idx) => (
                    <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="font-medium text-gray-700">{endpoint.endpoint}</span>
                      <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                        {endpoint.requests} requests
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && history && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Endpoint
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Method
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Response Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {history.logs && history.logs.length > 0 ? (
                    history.logs.map((log, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {log.endpoint}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          <span className={`px-2 py-1 rounded text-white text-xs font-semibold ${
                            log.method === 'GET' ? 'bg-blue-500' :
                            log.method === 'POST' ? 'bg-green-500' :
                            log.method === 'PUT' ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}>
                            {log.method}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            log.status >= 200 && log.status < 300 ? 'bg-green-100 text-green-800' :
                            log.status >= 400 && log.status < 500 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {log.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {log.response_time_ms.toFixed(2)}ms
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                        No requests yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Showing {history.logs?.length || 0} of {history.total} total requests
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
