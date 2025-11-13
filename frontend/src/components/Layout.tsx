import React from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  Calculator, 
  Shield, 
  MessageSquare, 
  LogOut, 
  User,
  TrendingUp
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

const Layout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Tax Calculator', href: '/tax', icon: Calculator },
    { name: 'Anomaly Detection', href: '/documents', icon: Shield },
    { name: 'AI Assistant', href: '/chatbot', icon: MessageSquare }
  ]

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Sidebar */}
      <motion.div
        initial={{ x: -300 }}
        animate={{ x: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg border-r border-gray-200"
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center px-6 py-8">
            <div className="flex items-center">
              <div className="p-2 bg-gradient-to-r from-gray-700 to-gray-900 rounded-xl mr-3">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">AI Tax</h1>
                <p className="text-xs text-gray-600">Assistant</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 space-y-2">
            {navigation.map((item) => (
              <motion.button
                key={item.name}
                onClick={() => navigate(item.href)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all ${
                  isActive(item.href)
                    ? 'bg-gradient-to-r from-gray-700 to-gray-900 text-white shadow-lg'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </motion.button>
            ))}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-gradient-to-r from-gray-600 to-gray-800 rounded-lg mr-3">
                <User className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                <p className="text-xs text-gray-600">{user?.email}</p>
              </div>
            </div>
            <motion.button
              onClick={handleLogout}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full flex items-center px-4 py-2 text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
            >
              <LogOut className="w-4 h-4 mr-3" />
              Sign Out
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="pl-64">
        <motion.main
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="min-h-screen"
        >
          <Outlet />
        </motion.main>
      </div>
    </div>
  )
}

export default Layout