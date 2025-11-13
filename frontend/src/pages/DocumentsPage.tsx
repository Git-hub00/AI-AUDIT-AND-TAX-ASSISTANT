import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Shield, 
  Upload, 
  AlertTriangle, 
  CheckCircle, 
  FileText,
  TrendingUp,
  Eye,
  Download
} from 'lucide-react'
import { api } from '../services/api'

interface Transaction {
  id: number
  date: string
  amount: number
  merchant: string
  category: string
  anomalyScore: number
  description: string
}

interface AnomalyResult {
  transactions: Transaction[]
  summary: {
    totalTransactions: number
    anomaliesDetected: number
    totalAmount: number
  }
}

const DocumentsPage: React.FC = () => {
  const [files, setFiles] = useState<File[]>([])
  const [result, setResult] = useState<AnomalyResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const handleAnalyze = async () => {
    if (files.length === 0) {
      setError('Please upload at least one file')
      return
    }

    setLoading(true)
    setError('')

    try {
      console.log('Sending files for analysis:', files.map(f => f.name))
      const response = await api.post('/audit/anomaly/detect', { files: files.map(f => f.name) })
      console.log('Analysis response:', response.data)
      setResult(response.data)
    } catch (error: any) {
      console.error('Analysis error:', error)
      const errorMessage = error.response?.data?.detail || error.response?.data?.error || error.message || 'Analysis failed'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const getRiskLevel = (score: number) => {
    if (score > 0.7) return { level: 'High', color: 'text-red-400', bg: 'bg-red-500/20' }
    if (score > 0.4) return { level: 'Medium', color: 'text-yellow-400', bg: 'bg-yellow-500/20' }
    return { level: 'Low', color: 'text-green-400', bg: 'bg-green-500/20' }
  }

  const handleDownloadReport = async (format: 'pdf' | 'csv') => {
    if (!result) return
    
    try {
      const response = await fetch('http://localhost:8000/api/audit/export-report-public', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...result,
          format
        })
      })
      
      if (!response.ok) {
        throw new Error('Download failed')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audit_report_${new Date().toISOString().split('T')[0]}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download error:', error)
      setError('Failed to download report')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">

      <div className="relative z-10 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="flex items-center mb-4">
            <div className="p-3 bg-gradient-to-r from-red-600 to-red-800 rounded-2xl mr-4">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Anomaly Detection</h1>
              <p className="text-gray-600 text-lg">AI-powered fraud and anomaly detection</p>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-1"
          >
            <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <FileText className="w-6 h-6 mr-3" />
                Upload Documents
              </h2>

              <div className="mb-6">
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-gray-400 transition-colors">
                  <Upload className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                  <input
                    type="file"
                    multiple
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                    accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-gray-900 font-medium text-lg">Click to upload</span>
                    <p className="text-gray-500 mt-2">or drag and drop files here</p>
                  </label>
                  <p className="text-xs text-gray-500 mt-4">
                    Supported: PDF, Images, CSV, Excel
                  </p>
                </div>

                {files.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <h3 className="text-gray-900 font-medium">Uploaded Files:</h3>
                    {files.map((file, index) => (
                      <div key={index} className="flex items-center text-sm text-gray-700 bg-gray-50 rounded-lg p-3">
                        <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                        <span className="flex-1">{file.name}</span>
                        <span className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {error && (
                <div className="bg-red-100 border border-red-300 rounded-lg p-3 text-red-700 text-sm mb-4">
                  {error}
                </div>
              )}

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleAnalyze}
                disabled={loading || files.length === 0}
                className="w-full py-3 bg-gradient-to-r from-red-600 to-red-800 text-white font-semibold rounded-lg hover:from-red-700 hover:to-red-900 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                    Analyzing...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <Shield className="w-5 h-5 mr-2" />
                    Detect Anomalies
                  </div>
                )}
              </motion.button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="lg:col-span-2"
          >
            {result ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-600 text-sm">Total Transactions</p>
                        <p className="text-2xl font-bold text-gray-900">{result.summary.totalTransactions}</p>
                      </div>
                      <FileText className="w-8 h-8 text-blue-600" />
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-600 text-sm">Anomalies Detected</p>
                        <p className="text-2xl font-bold text-red-600">{result.summary.anomaliesDetected}</p>
                      </div>
                      <AlertTriangle className="w-8 h-8 text-red-600" />
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-600 text-sm">Total Amount</p>
                        <p className="text-2xl font-bold text-green-600">₹{result.summary.totalAmount.toLocaleString()}</p>
                      </div>
                      <TrendingUp className="w-8 h-8 text-green-600" />
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="text-xl font-bold text-gray-900 flex items-center">
                      <Eye className="w-5 h-5 mr-3" />
                      Transaction Analysis
                    </h3>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-4 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Date</th>
                          <th className="px-6 py-4 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Description</th>
                          <th className="px-6 py-4 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Merchant</th>
                          <th className="px-6 py-4 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Amount</th>
                          <th className="px-6 py-4 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Risk Level</th>
                          <th className="px-6 py-4 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {result.transactions.map((transaction) => {
                          const risk = getRiskLevel(transaction.anomalyScore)
                          return (
                            <tr key={transaction.id} className="hover:bg-gray-50 transition-colors">
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                {transaction.date}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-900">
                                {transaction.description}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                {transaction.merchant}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                ₹{transaction.amount.toLocaleString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${risk.bg} ${risk.color}`}>
                                  {risk.level}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                {(transaction.anomalyScore * 100).toFixed(1)}%
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                  
                  <div className="p-6 border-t border-gray-200">
                    <div className="flex gap-3">
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleDownloadReport('pdf')}
                        className="flex items-center px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg transition-colors"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download PDF
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleDownloadReport('csv')}
                        className="flex items-center px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-300 rounded-lg transition-colors"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download CSV
                      </motion.button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl p-12 border border-gray-200 shadow-sm text-center">
                <Shield className="w-20 h-20 text-gray-500 mx-auto mb-6" />
                <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                  Ready to Analyze
                </h3>
                <p className="text-gray-600 text-lg">
                  Upload your financial documents to detect anomalies and suspicious patterns
                </p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  )
}

export default DocumentsPage