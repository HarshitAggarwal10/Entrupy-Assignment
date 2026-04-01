import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import ProductList from './components/ProductList';
import Notifications from './components/Notifications';
import './index.css';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const navigation = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'products', label: 'Products', icon: '📦' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-blue-600">💰 Price Monitor</h1>
            </div>
            <div className="flex gap-1 sm:gap-4">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`px-3 sm:px-4 py-2 rounded-md text-sm font-medium transition ${
                    currentPage === item.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <span className="hidden sm:inline">{item.icon} {item.label}</span>
                  <span className="sm:hidden">{item.icon}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main>
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'products' && <ProductList />}
        {currentPage === 'notifications' && <Notifications />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 text-center text-gray-600 text-sm">
        <p>Product Price Monitoring System © 2024</p>
      </footer>
    </div>
  );
}

export default App;
