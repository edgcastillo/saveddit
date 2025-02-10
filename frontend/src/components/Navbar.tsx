import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/auth/exports';
import LoginModal from './LoginModal';

export default function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

  return (
    <nav className="bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/saveddit" className="text-xl font-bold text-gray-800">
              Saveddit
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            {!isAuthenticated ? (
              <>
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="text-gray-600 hover:text-gray-900"
                >
                  Login
                </button>
                <Link
                  to="/saveddit/create-account"
                  className="bg-blue-600 text-white font-semibold px-4 py-2 rounded-md hover:bg-blue-700 shadow-sm text-shadow"
                >
                  Create Account
                </Link>
              </>
            ) : (
              <button
                onClick={logout}
                className="text-gray-600 hover:text-gray-900"
              >
                Logout
              </button>
            )}
          </div>
        </div>
      </div>
      <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
    </nav>
  );
} 