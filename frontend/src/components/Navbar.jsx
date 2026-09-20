import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MessageSquare, Database, LogOut, User as UserIcon } from 'lucide-react';

export const Navbar = () => {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 px-4 py-3 shadow-sm">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        {/* Brand / Logo */}
        <Link to="/chat" className="flex items-center space-x-2 text-xl font-bold tracking-tight text-white hover:text-brand-100 transition-colors">
          <MessageSquare className="w-6 h-6 text-brand-500" />
          <span>AI RAG Chatbot</span>
        </Link>

        {/* Navigation Actions */}
        <div className="flex items-center space-x-4">
          {/* User Badge */}
          <div className="flex items-center space-x-2 bg-slate-800 px-3 py-1.5 rounded-full text-xs text-slate-300 border border-slate-700">
            <UserIcon className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-medium">{user?.email}</span>
            {isAdmin && (
              <span className="bg-amber-500/20 text-amber-300 font-semibold px-2 py-0.5 rounded text-[10px] uppercase border border-amber-500/30">
                Admin
              </span>
            )}
          </div>

          {/* Navigation Items */}
          <div className="flex items-center space-x-2">
            <Link
              to="/chat"
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                location.pathname === '/chat'
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              Chat Area
            </Link>

            {isAdmin && (
              <Link
                to="/admin"
                className={`flex items-center space-x-1 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  location.pathname.startsWith('/admin')
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                <span>Knowledge Base</span>
              </Link>
            )}

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/20 rounded-md transition-colors"
              title="Logout"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
