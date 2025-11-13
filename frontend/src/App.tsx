import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import DocumentsPage from './pages/DocumentsPage'
import TaxPage from './pages/TaxPage'
import ChatbotPage from './pages/ChatbotPage'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} />
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />} 
      />
      <Route 
        path="/register" 
        element={isAuthenticated ? <Navigate to="/dashboard" /> : <RegisterPage />} 
      />
      
      {/* Dashboard route - accessible to all but with limited functionality */}
      <Route 
        path="/dashboard" 
        element={isAuthenticated ? <Layout /> : <DashboardPage />}
      >
        {isAuthenticated && <Route index element={<DashboardPage />} />}
      </Route>

      <Route 
        path="/documents" 
        element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}
      >
        <Route index element={<DocumentsPage />} />
      </Route>
      
      <Route 
        path="/tax" 
        element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}
      >
        <Route index element={<TaxPage />} />
      </Route>
      
      <Route 
        path="/chatbot" 
        element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}
      >
        <Route index element={<ChatbotPage />} />
      </Route>

      
      {/* Catch all route */}
      <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
    </Routes>
  )
}

export default App