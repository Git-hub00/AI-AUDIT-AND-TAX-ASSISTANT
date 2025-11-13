import React, { useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { api } from '../services/api'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, User, TrendingUp, Mic, MicOff } from 'lucide-react'
import { useVoiceCommands } from '../hooks/useVoiceCommands'

const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentField, setCurrentField] = useState<'name' | 'email' | 'password' | 'confirmPassword'>('name')
  const navigate = useNavigate()
  const login = useAuthStore(state => state.login)
  
  const nameRef = useRef<HTMLInputElement>(null)
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const confirmPasswordRef = useRef<HTMLInputElement>(null)

  const { isListening, startListening, stopListening, isSupported } = useVoiceCommands({
    onNameCommand: (nameText) => {
      setFormData(prev => ({ ...prev, name: nameText }))
      setCurrentField('name')
      nameRef.current?.focus()
    },
    onEmailCommand: (emailText) => {
      setFormData(prev => ({ ...prev, email: emailText.replace(/\s+/g, '').toLowerCase() }))
      setCurrentField('email')
      emailRef.current?.focus()
    },
    onPasswordCommand: (passwordText) => {
      setFormData(prev => ({ ...prev, password: passwordText.replace(/\s+/g, '') }))
      setCurrentField('password')
      passwordRef.current?.focus()
    },
    onConfirmPasswordCommand: (passwordText) => {
      setFormData(prev => ({ ...prev, confirmPassword: passwordText.replace(/\s+/g, '') }))
      setCurrentField('confirmPassword')
      confirmPasswordRef.current?.focus()
    },
    onSignInCommand: () => {
      navigate('/login')
    },
    onSignUpCommand: () => {
      if (formData.name && formData.email && formData.password && formData.confirmPassword) {
        handleSubmit(new Event('submit') as any)
      }
    },
    onGoToSignUpCommand: () => {},
    onNextCommand: () => {
      switch (currentField) {
        case 'name':
          setCurrentField('email')
          emailRef.current?.focus()
          break
        case 'email':
          setCurrentField('password')
          passwordRef.current?.focus()
          break
        case 'password':
          setCurrentField('confirmPassword')
          confirmPasswordRef.current?.focus()
          break
        case 'confirmPassword':
          if (formData.name && formData.email && formData.password && formData.confirmPassword) {
            handleSubmit(new Event('submit') as any)
          }
          break
      }
    }
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      console.log('Attempting registration for:', formData.email)
      const registerResponse = await api.post('/auth/register', {
        name: formData.name,
        email: formData.email,
        password: formData.password
      })
      console.log('Registration response:', registerResponse.data)

      // Auto login after registration
      const loginResponse = await api.post('/auth/login', {
        email: formData.email,
        password: formData.password
      })
      console.log('Auto-login response:', loginResponse.data)

      const { access_token } = loginResponse.data
      const profileResponse = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      })
      console.log('Profile response:', profileResponse.data)

      login(profileResponse.data, access_token)
      navigate('/dashboard')
    } catch (error: any) {
      console.error('Registration error:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed. Please try again.'
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Join AI Tax Assistant</h1>
          <p className="text-gray-600">Create your account to get started</p>
        </motion.div>

        {/* Register Form */}
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

            {/* Name Field */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  ref={nameRef}
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  onFocus={() => setCurrentField('name')}
                  className={`w-full pl-10 pr-4 py-3 bg-white border rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent transition-all ${
                    currentField === 'name' ? 'border-gray-500/50' : 'border-gray-300'
                  }`}
                  placeholder="Say your full name or type it"
                  required
                />
              </div>
            </div>

            {/* Email Field */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  ref={emailRef}
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  onFocus={() => setCurrentField('email')}
                  className={`w-full pl-10 pr-4 py-3 bg-white border rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent transition-all ${
                    currentField === 'email' ? 'border-gray-500/50' : 'border-gray-300'
                  }`}
                  placeholder="Say 'email' then your email address"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  ref={passwordRef}
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  onFocus={() => setCurrentField('password')}
                  className={`w-full pl-10 pr-12 py-3 bg-white border rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent transition-all ${
                    currentField === 'password' ? 'border-gray-500/50' : 'border-gray-300'
                  }`}
                  placeholder="Say 'password' then your password"
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

            {/* Confirm Password Field */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  ref={confirmPasswordRef}
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  onFocus={() => setCurrentField('confirmPassword')}
                  className={`w-full pl-10 pr-4 py-3 bg-white border rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent transition-all ${
                    currentField === 'confirmPassword' ? 'border-gray-500/50' : 'border-gray-300'
                  }`}
                  placeholder="Say 'confirm password' then repeat password"
                  required
                />
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
                  Creating account...
                </div>
              ) : (
                'Create Account'
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
                Current field: <span className="text-gray-700 font-medium">{currentField}</span>
              </p>
              <p className="text-xs text-gray-500">
                Say: "email [address]", "password [text]", "confirm password [text]", "next", or "sign up"
              </p>
            </div>
          )}

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Already have an account?{' '}
              <Link 
                to="/login" 
                className="text-gray-700 hover:text-gray-900 font-medium transition-colors"
              >
                Sign in
              </Link>
            </p>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default RegisterPage