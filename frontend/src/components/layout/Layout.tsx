import React, { ReactNode } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/button';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-bold text-gray-900">Knods Token Wallet</h1>
            
            {isAuthenticated ? (
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">
                  {user?.email}
                </span>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={logout}
                >
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  asChild
                >
                  <a href="/login">Login</a>
                </Button>
                <Button 
                  size="sm"
                  asChild
                >
                  <a href="/register">Register</a>
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>
      
      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-sm text-gray-500 text-center">
            &copy; {new Date().getFullYear()} Knods Token Wallet. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
