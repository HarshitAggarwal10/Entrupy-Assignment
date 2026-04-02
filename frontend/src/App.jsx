import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import ProductList from './components/ProductList';
import Notifications from './components/Notifications';
import UsageStats from './components/UsageStats';
import ApiUsage from './components/ApiUsage';
import UserProfile from './components/UserProfile';
import Login from './components/Login';
import { authService, productService } from './services/api';
import './index.css';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [user, setUser] = useState(authService.getCurrentUser());
  const [token, setToken] = useState(authService.getToken());
  const [tokenValid, setTokenValid] = useState(true);
  const [showCacheWarning, setShowCacheWarning] = useState(false);

  // Validate token on app startup
  useEffect(() => {
    const validateToken = async () => {
      const currentToken = authService.getToken();
      if (currentToken) {
        try {
          // Try to validate token by making a test request
          const response = await productService.health();
          if (response.status === 200) {
            setTokenValid(true);
          }
        } catch (err) {
          console.warn('Token validation failed:', err.message);
          // If token is invalid, clear it
          authService.logout();
          setToken(null);
          setUser(null);
          setTokenValid(false);
          setShowCacheWarning(true);
        }
      }
    };

    validateToken();
  }, []);

  // Listen for storage changes (optional, but good for multi-tab sync)
  useEffect(() => {
    const handleStorageChange = () => {
      setToken(authService.getToken());
      setUser(authService.getCurrentUser());
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const handleLoginSuccess = (newToken, newUser) => {
    setToken(newToken);
    setUser(newUser);
    setTokenValid(true);
    setShowCacheWarning(false);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    authService.logout();
    setToken(null);
    setUser(null);
    setTokenValid(true);
  };

  const clearBrowserCache = () => {
    // Clear all storage
    localStorage.clear();
    sessionStorage.clear();
    // Clear app state
    authService.logout();
    setToken(null);
    setUser(null);
    setTokenValid(true);
    setShowCacheWarning(false);
    // Reload page
    window.location.reload();
  };

  if (!token) {
    return (
      <>
        {showCacheWarning && (
          <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
            <p className="font-bold">⚠️ Browser Cache Issue Detected</p>
            <p className="text-sm mt-1">Your browser cache was cleared due to an invalid token. Please login again.</p>
          </div>
        )}
        <Login onLoginSuccess={handleLoginSuccess} />
      </>
    );
  }

  const navigation = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'products', label: 'Products' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'usage', label: 'API Usage' },
  ];

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-blue-600">Price Monitor</h1>
            </div>
            <div className="hidden md:flex gap-1">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                    currentPage === item.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                   }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-4">
              {user && (
                <div className="text-sm text-right">
                  <p className="text-gray-900 font-bold">{user.full_name || user.username}</p>
                  <p className="text-gray-500 text-xs">{user.email}</p>
                </div>
              )}
              {/* <button
                onClick={clearBrowserCache}
                title="Clear browser cache and localStorage"
                className="px-2 py-2 rounded-md text-sm font-medium text-orange-600 hover:bg-orange-50 transition"
              >
                🗑️ Clear Cache
              </button> */}
              <button
                onClick={handleLogout}
                className="px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:bg-red-50 transition"
              >
                Logout
              </button>
            </div>
          </div>

          <div className="md:hidden flex gap-1 pb-3 overflow-x-auto">
            {navigation.map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id)}
                className={`px-3 py-2 rounded-md text-sm font-medium transition whitespace-nowrap ${
                  currentPage === item.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="flex-1">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'products' && <ProductList />}
        {currentPage === 'notifications' && <Notifications />}
        {currentPage === 'usage' && <UsageStats />}
      </main>

      <footer className="bg-white border-t border-gray-200 py-4 text-center text-gray-600 text-sm">
        <p>Entrupy Assignment</p>
        <p>Harshit Aggarwal | 2310990766 | [harshit0766.be23@chitkara.edu.in]</p>
      </footer>
    </div>
  );
}

export default App;