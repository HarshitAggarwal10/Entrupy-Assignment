import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import ProductList from './components/ProductList';
import Notifications from './components/Notifications';
import Login from './components/Login';
import ApiUsage from './components/ApiUsage';
import UserProfile from './components/UserProfile';
import './index.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      setIsAuthenticated(true);
      setUser(JSON.parse(storedUser));
    }
    
    setLoading(false);
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
    setCurrentPage('dashboard');
  };

  const navigation = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'products', label: 'Products' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'usage', label: 'API Usage' },
  ];

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left side - Logo */}
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-blue-600">Price Monitor</h1>
            </div>

            {/* Middle - Navigation */}
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

            {/* Right side - User menu */}
            <div className="flex items-center gap-4">
              {user && (
                <div className="text-sm">
                  <p className="text-gray-700 font-medium">{user.username}</p>
                </div>
              )}
              
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage('profile')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                    currentPage === 'profile'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  Profile
                </button>
                
                <button
                  onClick={handleLogout}
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-red-100 hover:text-red-700 transition"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>

          {/* Mobile navigation */}
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

      {/* Page Content */}
      <main className="flex-1">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'products' && <ProductList />}
        {currentPage === 'notifications' && <Notifications />}
        {currentPage === 'usage' && <ApiUsage />}
        {currentPage === 'profile' && <UserProfile />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 text-center text-gray-600 text-sm">
        <p>Product Price Monitoring System © 2024</p>
      </footer>
    </div>
  );
}

export default App;
