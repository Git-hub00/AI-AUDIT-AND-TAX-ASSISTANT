import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { api } from '../services/api'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, TrendingUp, Mic, MicOff } from 'lucide-react'
import { useVoiceCommands } from '../hooks/useVoiceCommands'

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const login = useAuthStore(state => state.login)

  const { isListening, startListening, stopListening, isSupported } = useVoiceCommands({
    onNameCommand: () => {}, // Not used in login
    onEmailCommand: (emailText) => {
      setEmail(emailText.replace(/\s+/g, '').toLowerCase())
    },
    onPasswordCommand: (passwordText) => {
      setPassword(passwordText.replace(/\s+/g, ''))
    },
    onSignInCommand: () => {
      if (email && password) {
        handleSubmit(new Event('submit') as any)
      }
    },
    onGoToSignUpCommand: () => {
      navigate('/register')
    },
    onSignUpCommand: () => {},
    onNextCommand: () => {}
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      console.log('Attempting login for:', email)
      const response = await api.post('/auth/login', { email, password })
      console.log('Login response:', response.data)
      
      const { access_token } = response.data
      
      // Get user profile
      const profileResponse = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      })
      console.log('Profile response:', profileResponse.data)
      
      login(profileResponse.data, access_token)
      navigate('/dashboard')
    } catch (error: any) {
      console.error('Login error:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed. Please try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Logo & Title */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-gray-700 to-gray-900 rounded-2xl mb-4">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Tax Assistant</h1>
          <p className="text-gray-600">Smart financial analysis at your fingertips</p>
        </motion.div>

        {/* Login Form */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-gray-200"
        >
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-red-100 border border-red-300 rounded-lg p-3 text-red-700 text-sm"
              >
                {error}
              </motion.div>
            )}

            {/* Email Field */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent transition-all"
                  placeholder="Say 'email' then your email address"
                  required
                />
              </div>
            </div>

            {/* PIN Field */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">6-Digit PIN</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent transition-all"
                  placeholder="Say 'password' then your PIN"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  minLength={6}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-gray-700 to-gray-900 text-white font-semibold rounded-lg hover:from-gray-800 hover:to-gray-950 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                  Signing in...
                </div>
              ) : (
                'Sign In'
              )}
            </motion.button>
          </form>

          {/* Voice Control */}
          {isSupported && (
            <div className="mt-4 text-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                type="button"
                onClick={isListening ? stopListening : startListening}
                className={`inline-flex items-center px-4 py-2 rounded-lg font-medium transition-all ${
                  isListening 
                    ? 'bg-red-500/20 text-red-300 border border-red-500/50' 
                    : 'bg-green-500/20 text-green-300 border border-green-500/50'
                }`}
              >
                {isListening ? <MicOff className="w-4 h-4 mr-2" /> : <Mic className="w-4 h-4 mr-2" />}
                {isListening ? 'Stop Voice' : 'Start Voice'}
              </motion.button>
              <p className="text-xs text-gray-500 mt-2">
                Say: "email [your email]", "password [your PIN]", "sign in", or "go to sign up page"
              </p>
            </div>
          )}

          {/* Register Link */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <Link 
                to="/register" 
                className="text-gray-700 hover:text-gray-900 font-medium transition-colors"
              >
                Sign up
              </Link>
            </p>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default LoginPage