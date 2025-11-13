import React, { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  FileText, 
  AlertTriangle, 
  DollarSign,
  Calculator,
  Shield,
  MessageSquare,
  BarChart3,
  PieChart,
  Activity
} from 'lucide-react'
import { api } from '../services/api'

interface DashboardStats {
  documents: number
  transactions: number
  anomalies: number
  taxSavings: number
}

const DashboardPage: React.FC = () => {
  const { user, token } = useAuthStore()
  const [stats, setStats] = useState<DashboardStats>({
    documents: 0,
    transactions: 0,
    anomalies: 0,
    taxSavings: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Test login function for debugging
  const handleTestLogin = async () => {
    try {
      console.log('Attempting test login...')
      const response = await api.post('/auth/login', {
        email: 'test@example.com',
        password: '123456'
      })
      
      console.log('Login response:', response.data)
      
      if (response.data.access_token) {
        const { login } = useAuthStore.getState()
        login(
          { 
            id: response.data.user?.id || 'test', 
            name: response.data.user?.name || 'Test User', 
            email: response.data.user?.email || 'test@example.com' 
          },
          response.data.access_token
        )
        
        // Force refresh stats after login
        setTimeout(() => {
          window.location.reload()
        }, 500)
      }
    } catch (error) {
      console.error('Test login failed:', error)
      setError('Login failed. Make sure backend is running and test user exists.')
    }
  }

  useEffect(() => {
    const fetchStats = async () => {
      if (!token) {
        console.log('No token available, skipping stats fetch')
        setLoading(false)
        return
      }

      try {
        console.log('Fetching dashboard stats...')
        const response = await api.get('/dashboard/stats')
        console.log('Dashboard stats response:', response.data)
        const data = response.data
        
        // Check if user has no data and create sample data
        const hasNoData = (data.documents?.total || 0) === 0 && 
                         (data.transactions?.total || 0) === 0 && 
                         (data.tax_records?.total || 0) === 0
        
        if (hasNoData) {
          console.log('No data found, creating sample data...')
          try {
            await api.post('/dashboard/create-sample-data')
            // Refetch stats after creating sample data
            const newResponse = await api.get('/dashboard/stats')
            const newData = newResponse.data
            setStats({
              documents: newData.documents?.total || 0,
              transactions: newData.transactions?.total || 0,
              anomalies: newData.anomaly_reports?.total || 0,
              taxSavings: Math.round(newData.tax_records?.total_income || 0)
            })
          } catch (sampleError) {
            console.error('Failed to create sample data:', sampleError)
            // Fall back to original data
            setStats({
              documents: data.documents?.total || 0,
              transactions: data.transactions?.total || 0,
              anomalies: data.anomaly_reports?.total || 0,
              taxSavings: Math.round(data.tax_records?.total_income || 0)
            })
          }
        } else {
          setStats({
            documents: data.documents?.total || 0,
            transactions: data.transactions?.total || 0,
            anomalies: data.anomaly_reports?.total || 0,
            taxSavings: Math.round(data.tax_records?.total_income || 0)
          })
        }
        setError(null)
      } catch (error: any) {
        console.error('Failed to fetch stats:', error)
        setError(error.response?.data?.detail || error.message || 'Failed to load dashboard data')
        // Set default values on error
        setStats({
          documents: 0,
          transactions: 0,
          anomalies: 0,
          taxSavings: 0
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [token])

  const features = [
    {
      icon: Calculator,
      title: 'Tax Calculator',
      description: 'AI-powered tax calculations with ML predictions',
      color: 'from-blue-600 to-blue-800',
      href: '/tax'
    },
    {
      icon: Shield,
      title: 'Anomaly Detection',
      description: 'Detect suspicious transactions and fraud patterns',
      color: 'from-red-600 to-red-800',
      href: '/documents'
    },
    {
      icon: MessageSquare,
      title: 'AI Assistant',
      description: 'Chat with AI about your financial documents',
      color: 'from-green-600 to-green-800',
      href: '/chatbot'
    }
  ]

  const statCards = [
    {
      title: 'Documents',
      value: stats.documents,
      icon: FileText,
      color: 'from-gray-600 to-gray-800',
      change: '+12%'
    },
    {
      title: 'Transactions',
      value: stats.transactions,
      icon: Activity,
      color: 'from-blue-600 to-blue-800',
      change: '+8%'
    },
    {
      title: 'Anomalies',
      value: stats.anomalies,
      icon: AlertTriangle,
      color: 'from-red-600 to-red-800',
      change: '-5%'
    },
    {
      title: 'Tax Savings',
      value: `₹${stats.taxSavings.toLocaleString()}`,
      icon: DollarSign,
      color: 'from-green-600 to-green-800',
      change: '+15%'
    }
  ]

  // Debug logging
  console.log('Dashboard render - Auth state:', { user, token: token ? 'present' : 'missing', loading, error })

  // Fallback for white screen issues
  if (typeof window === 'undefined') {
    return <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-white">Loading...</div>
    </div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Welcome to AI Tax Assistant
          </h1>
          <p className="text-gray-600 text-lg">
            Your intelligent financial analysis dashboard
          </p>
          {error && (
            <div className="mt-4 p-4 bg-red-100 border border-red-300 rounded-lg">
              <p className="text-red-700 text-sm">
                ⚠️ {error}
              </p>
            </div>
          )}
          {token && (
            <div className="mt-4">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded-lg text-sm transition-colors"
              >
                🔄 Refresh Dashboard
              </button>
            </div>
          )}
          {!token && (
            <div className="mt-4 p-4 bg-yellow-100 border border-yellow-300 rounded-lg">
              <p className="text-yellow-700 text-sm mb-3">
                🔐 Please log in to view your dashboard statistics
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleTestLogin}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors"
                >
                  Test Login (Debug)
                </button>
                <button
                  onClick={() => window.location.href = '/login'}
                  className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm transition-colors"
                >
                  Go to Login
                </button>
              </div>
            </div>
          )}
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          {statCards.map((stat, index) => {
            const displayValue = loading ? '...' : 
              !token ? '🔒' : 
              (typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value)
            
            return (
              <motion.div
                key={stat.title}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.1 * index }}
                whileHover={{ scale: 1.05 }}
                className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-xl bg-gradient-to-r ${stat.color}`}>
                    <stat.icon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-green-600 text-sm font-medium">
                    {!token ? '' : stat.change}
                  </span>
                </div>
                <h3 className="text-gray-600 text-sm font-medium mb-1">
                  {stat.title}
                </h3>
                <p className="text-2xl font-bold text-gray-900">
                  {displayValue}
                </p>
                {!token && (
                  <p className="text-xs text-gray-500 mt-1">
                    Login to view data
                  </p>
                )}
              </motion.div>
            )
          })}
        </motion.div>

        {/* Feature Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
        >
          {features.map((feature, index) => (
            <motion.a
              key={feature.title}
              href={feature.href}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 * index }}
              whileHover={{ scale: 1.02, y: -5 }}
              className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm group cursor-pointer"
            >
              <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-r ${feature.color} mb-6 group-hover:scale-110 transition-transform`}>
                <feature.icon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
              <div className="mt-6 flex items-center text-gray-700 group-hover:text-gray-900 transition-colors">
                <span className="text-sm font-medium">Get Started</span>
                <TrendingUp className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </div>
            </motion.a>
          ))}
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: FileText, label: 'Upload Document', color: 'bg-blue-600' },
              { icon: Calculator, label: 'Calculate Tax', color: 'bg-green-600' },
              { icon: BarChart3, label: 'View Reports', color: 'bg-gray-600' },
              { icon: PieChart, label: 'Analytics', color: 'bg-indigo-600' }
            ].map((action, index) => (
              <motion.button
                key={action.label}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-200"
              >
                <div className={`p-2 rounded-lg ${action.color} mr-3`}>
                  <action.icon className="w-5 h-5 text-white" />
                </div>
                <span className="text-gray-900 font-medium">{action.label}</span>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default DashboardPage