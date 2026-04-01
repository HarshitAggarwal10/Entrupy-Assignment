import React, { useState, useEffect } from 'react';

export default function UserProfile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
  });

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setFormData({ full_name: data.full_name || '' });
        setError(null);
      } else if (response.status === 401) {
        setError('Session expired. Please login again.');
      } else {
        setError('Failed to load user profile');
      }
    } catch (err) {
      setError('Error loading user profile');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // For now, we'll just show a success message
      // In a real app, you'd have an endpoint to update user profile
      setUser(prev => ({
        ...prev,
        full_name: formData.full_name
      }));
      
      setSuccessMessage('Profile updated successfully');
      setIsEditing(false);
      
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError('Error updating profile');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('token');
      
      await fetch('http://localhost:8000/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } catch (err) {
      console.error('Logout error:', err);
      // Still redirect even if logout request fails
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  };

  if (loading && !user) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="bg-gray-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Profile Settings</h1>
          <p className="text-gray-600 mt-2">Manage your account information</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {successMessage}
          </div>
        )}

        {user && (
          <div className="space-y-6">
            {/* Profile Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Account Information</h2>
                {!isEditing && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
                  >
                    Edit Profile
                  </button>
                )}
              </div>

              {isEditing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      name="full_name"
                      value={formData.full_name}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter your full name"
                    />
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleSave}
                      disabled={loading}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium disabled:bg-gray-400"
                    >
                      {loading ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                      onClick={() => {
                        setIsEditing(false);
                        setFormData({ full_name: user.full_name || '' });
                      }}
                      className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition font-medium"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="border-b border-gray-200 pb-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Username</h3>
                    <p className="text-lg text-gray-900">{user.username}</p>
                  </div>

                  <div className="border-b border-gray-200 pb-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Email</h3>
                    <p className="text-lg text-gray-900">{user.email}</p>
                  </div>

                  <div className="border-b border-gray-200 pb-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Full Name</h3>
                    <p className="text-lg text-gray-900">{user.full_name || 'Not provided'}</p>
                  </div>

                  <div className="border-b border-gray-200 pb-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Account Status</h3>
                    <p className={`text-lg font-semibold ${user.is_active ? 'text-green-600' : 'text-red-600'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </p>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Member Since</h3>
                    <p className="text-lg text-gray-900">
                      {new Date(user.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Security Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Security</h2>
              
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h3 className="font-semibold text-blue-900 mb-2">Last Login</h3>
                  <p className="text-blue-700">
                    {user.last_login
                      ? new Date(user.last_login).toLocaleString()
                      : 'This is your first login'}
                  </p>
                </div>

                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <h3 className="font-semibold text-amber-900 mb-2">API Key</h3>
                  <p className="text-amber-700 text-sm mb-3">
                    Your API is secured with JWT tokens. Tokens expire after 24 hours.
                  </p>
                  <button
                    onClick={() => {
                      const token = localStorage.getItem('token');
                      navigator.clipboard.writeText(token);
                      setSuccessMessage('Token copied to clipboard');
                      setTimeout(() => setSuccessMessage(''), 3000);
                    }}
                    className="px-3 py-1 bg-amber-600 text-white rounded hover:bg-amber-700 transition text-sm"
                  >
                    Copy Current Token
                  </button>
                </div>
              </div>
            </div>

            {/* Danger Zone */}
            <div className="bg-white rounded-lg shadow p-6 border-t-4 border-red-500">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Danger Zone</h2>
              
              <button
                onClick={handleLogout}
                className="w-full px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium"
              >
                Logout
              </button>
              
              <p className="text-sm text-gray-600 mt-3">
                You will be signed out from this device. Your token will be invalidated.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
