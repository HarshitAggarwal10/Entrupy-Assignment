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
  const [unprocessedCount, setUnprocessedCount] = useState(0);
  const [prevCount, setPrevCount] = useState(0);
  const [showAlert, setShowAlert] = useState(false);
  const [initialLoadDone, setInitialLoadDone] = useState(false);

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

  // Fetch unprocessed notification count periodically and show alerts
  useEffect(() => {
    const fetchUnprocessedCount = async () => {
      try {
        const response = await productService.getNotifications({
          is_processed: false,
          limit: 1,
        });
        const count = response.data.total || 0;
        
        // If we've loaded before and count increased, show alert
        if (initialLoadDone && count > unprocessedCount) {
          const newNotifications = count - unprocessedCount;
          console.log(`🔔 New notifications detected: ${newNotifications}`);
          
          // Show visual alert
          setShowAlert(true);
          setTimeout(() => setShowAlert(false), 5000);
          
          // Request browser notification permission if not already granted
          if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
          }
          
          // Show browser notification if permitted
          if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Price Change Detected! 🔔', {
              body: `${newNotifications} new price change${newNotifications > 1 ? 's' : ''} detected. Check the Notifications tab!`,
              icon: '/favicon.ico'
            });
          }
          
          // Play a subtle sound alert
          try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
          } catch (e) {
            console.warn('Could not play notification sound');
          }
        }
        
        setUnprocessedCount(count);
        if (!initialLoadDone) {
          setInitialLoadDone(true);
        }
      } catch (err) {
        console.warn('Failed to fetch notification count:', err);
      }
    };

    // Fetch immediately
    if (token) {
      fetchUnprocessedCount();
    }

    // Set up interval to refresh every 5 seconds for faster detection
    const interval = setInterval(() => {
      if (token) {
        fetchUnprocessedCount();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [token, unprocessedCount, initialLoadDone]);

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
                  className={`px-4 py-2 rounded-md text-sm font-medium transition relative ${
                    currentPage === item.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                   }`}
                >
                  {item.label}
                  {item.id === 'notifications' && unprocessedCount > 0 && (
                    <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
                      {unprocessedCount}
                    </span>
                  )}
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
                className={`px-3 py-2 rounded-md text-sm font-medium transition whitespace-nowrap relative ${
                  currentPage === item.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.label}
                {item.id === 'notifications' && unprocessedCount > 0 && (
                  <span className="absolute top-0 right-0 inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
                    {unprocessedCount}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {showAlert && (
        <div className="bg-yellow-100 border-l-4 border-yellow-400 text-yellow-800 p-4 animate-slide-down">
          <p className="font-bold">🔔 Price Change Alert!</p>
          <p className="text-sm mt-1">New price changes detected! Check the Notifications tab for details.</p>
        </div>
      )}

      <main className="flex-1">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'products' && <ProductList />}
        {currentPage === 'notifications' && <Notifications onProcessNotifications={() => setUnprocessedCount(0)} />}
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