import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Calculator, 
  Upload, 
  FileText, 
  DollarSign, 
  TrendingUp,
  PieChart,
  BarChart3,
  CheckCircle,
  Download,
  Receipt,
  AlertTriangle,
  FileSpreadsheet
} from 'lucide-react'
import { api } from '../services/api'

interface TaxResult {
  totalIncome: number
  salaryIncome: number
  businessIncome: number
  deductions: number
  taxableIncome: number
  predictedTax: number
  effectiveRate: number
  confidence: number
  method: string
  breakdown: Array<{
    slab: string
    rate: string
    tax: number
    income: number
  }>
  recommendations: string[]
  savings: {
    currentTax: number
    potentialSavings: number
    optimizedDeductions: number
  }
  explainability?: {
    top_features: Array<{
      feature: string
      impact: number
      value: number
      description?: string
    }>
  }
  transaction_analysis?: {
    transactions: Array<{
      transaction_id: number
      amount: number
      category: string
      type: string
      tax_impact: number
      tax_rate: string
      deductible: boolean
      receipt_required: boolean
      compliance_notes: string[]
      tax_calculation: {
        base_amount: number
        applicable_rate: number
        calculated_tax: number
        effective_rate: number
      }
    }>
    receipt_requirements: Array<{
      transaction_id: number
      amount: number
      category: string
      reason: string
    }>
    summary: {
      total_transactions: number
      receipt_required_count: number
      total_tax_impact: number
      deductible_transactions: number
      average_tax_rate: number
    }
  }
}

const TaxPage: React.FC = () => {
  const [formData, setFormData] = useState({
    salary: '',
    business: '',
    deductions: ''
  })
  const [files, setFiles] = useState<File[]>([])
  const [result, setResult] = useState<TaxResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const requestData = {
        ...formData,
        files: files.map(f => f.name)
      }
      const response = await api.post('/tax/predict', requestData)
      setResult(response.data)
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Tax calculation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleExportReport = async (format: 'pdf' | 'csv') => {
    if (!result) return
    
    try {
      // Get auth token from localStorage
      const authData = localStorage.getItem('auth-storage')
      let token = ''
      if (authData) {
        try {
          const { state } = JSON.parse(authData)
          token = state?.token || ''
        } catch (e) {
          console.error('Error parsing auth data:', e)
        }
      }
      
      // Make API call to public endpoint (no auth required)
      const response = await fetch(`http://localhost:8000/api/tax/export-report-public?format=${format}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(result)
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }
      
      // Get the blob from response
      const blob = await response.blob()
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tax_report_${new Date().toISOString().split('T')[0]}.${format}`
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      console.log(`${format.toUpperCase()} report downloaded successfully`)
      
    } catch (error: any) {
      console.error('Export error:', error)
      setError(`Export failed: ${error.message || 'Unknown error'}`)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="flex items-center mb-4">
            <div className="p-3 bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl mr-4">
              <Calculator className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Tax Calculator</h1>
              <p className="text-gray-600 text-lg">AI-powered tax calculations with ML predictions</p>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <FileText className="w-6 h-6 mr-3" />
              Income Details
            </h2>

            {/* File Upload */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Upload Documents (Optional)
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-gray-400 transition-colors">
                <Upload className="w-8 h-8 text-gray-500 mx-auto mb-3" />
                <input
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                  accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="text-gray-900 font-medium">Click to upload</span>
                  <span className="text-gray-500"> or drag and drop</span>
                </label>
                <p className="text-xs text-gray-500 mt-2">
                  PDF, Images, CSV, Excel files
                </p>
              </div>
              {files.length > 0 && (
                <div className="mt-3 space-y-2">
                  <div className="text-xs text-blue-400 mb-2">
                    {files.length} file{files.length > 1 ? 's' : ''} ready for ML processing
                  </div>
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between text-sm text-gray-300 bg-white/5 rounded px-2 py-1">
                      <div className="flex items-center">
                        <CheckCircle className="w-4 h-4 text-green-400 mr-2" />
                        <span className="truncate">{file.name}</span>
                      </div>
                      <span className="text-xs text-gray-400">
                        {(file.size / 1024).toFixed(1)}KB
                      </span>
                    </div>
                  ))}
                  <div className="text-xs text-gray-400 mt-2">
                    💡 Files will be processed using OCR + NLP for income extraction
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-200 text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Salary Income (₹)
                  </label>
                  <input
                    type="number"
                    name="salary"
                    value={formData.salary}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your salary income"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Business Income (₹)
                  </label>
                  <input
                    type="number"
                    name="business"
                    value={formData.business}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your business income"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Total Deductions (₹)
                  </label>
                  <input
                    type="number"
                    name="deductions"
                    value={formData.deductions}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your total deductions"
                  />
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-800 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-blue-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                    Calculating...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <Calculator className="w-5 h-5 mr-2" />
                    Calculate Tax
                  </div>
                )}
              </motion.button>
            </form>
          </motion.div>

          {/* Results */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="space-y-6"
          >
            {/* Export Buttons - Top */}
            {result && (
              <div className="flex gap-2 justify-end">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleExportReport('csv')}
                  className="flex items-center px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                >
                  <FileSpreadsheet className="w-4 h-4 mr-1" />
                  CSV
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleExportReport('pdf')}
                  className="flex items-center px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
                >
                  <Download className="w-4 h-4 mr-1" />
                  PDF
                </motion.button>
              </div>
            )}
            {result ? (
              <>
                {/* Tax Summary */}
                <div className="glass rounded-2xl p-8 border border-white/20">
                  <h2 className="text-2xl font-bold text-black mb-6 flex items-center">
                    <DollarSign className="w-6 h-6 mr-3" />
                    Tax Calculation
                  </h2>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between items-center py-3 border-b border-white/10">
                      <span className="text-black">Total Income</span>
                      <span className="text-black font-semibold">₹{result.totalIncome.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center py-3 border-b border-white/10">
                      <span className="text-black">Total Deductions</span>
                      <span className="text-black font-semibold">₹{result.deductions.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center py-3 border-b border-white/10">
                      <span className="text-black">Taxable Income</span>
                      <span className="text-black font-semibold">₹{result.taxableIncome.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center py-3 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-lg px-4">
                      <div className="flex flex-col">
                        <span className="text-black font-medium">Predicted Tax</span>
                        <span className="text-xs text-black">Using {result.method}</span>
                      </div>
                      <span className="text-2xl font-bold text-green-400">₹{result.predictedTax.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center py-3">
                      <span className="text-black">Model Confidence</span>
                      <div className="flex items-center">
                        <div className="w-20 h-2 bg-gray-600 rounded-full mr-2">
                          <div 
                            className="h-2 bg-gradient-to-r from-yellow-400 to-green-400 rounded-full" 
                            style={{ width: `${result.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-black font-semibold">{(result.confidence * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center py-3">
                      <span className="text-black">Effective Rate</span>
                      <span className="text-black font-semibold">{result.effectiveRate.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>

                {/* Tax Slab Breakdown */}
                <div className="glass rounded-2xl p-8 border border-white/20">
                  <h3 className="text-xl font-bold text-black mb-6 flex items-center">
                    <BarChart3 className="w-5 h-5 mr-3" />
                    Tax Slab Breakdown
                  </h3>
                  
                  <div className="space-y-3">
                    {result.breakdown.map((slab, index) => (
                      <div key={index} className="flex justify-between items-center py-2 px-3 bg-white/5 rounded-lg">
                        <div className="flex flex-col">
                          <span className="text-black font-medium">{slab.slab}</span>
                          <span className="text-xs text-black">Rate: {slab.rate}</span>
                        </div>
                        <div className="text-right">
                          <div className="text-black font-semibold">₹{slab.tax.toLocaleString()}</div>
                          <div className="text-xs text-black">₹{slab.income.toLocaleString()}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* ML Model Insights */}
                {result.explainability && result.explainability.top_features && (
                  <div className="glass rounded-2xl p-8 border border-white/20">
                    <h3 className="text-xl font-bold text-black mb-6 flex items-center">
                      <TrendingUp className="w-5 h-5 mr-3" />
                      ML Model Insights
                    </h3>
                    
                    <div className="space-y-3">
                      {result.explainability.top_features.slice(0, 5).map((feature: any, index: number) => (
                        <div key={index} className="flex justify-between items-center py-2">
                          <span className="text-black capitalize">
                            {feature.feature.replace('_', ' ')}
                          </span>
                          <div className="flex items-center">
                            <div className={`w-16 h-2 rounded-full mr-2 ${
                              feature.impact > 0 ? 'bg-red-500' : 'bg-green-500'
                            }`} style={{
                              width: `${Math.min(Math.abs(feature.impact) / Math.max(...result.explainability.top_features.map((f: any) => Math.abs(f.impact))) * 60, 60)}px`
                            }}></div>
                            <span className={`text-sm font-medium ${
                              feature.impact > 0 ? 'text-red-400' : 'text-green-400'
                            }`}>
                              {feature.impact > 0 ? '+' : ''}{feature.impact.toFixed(0)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Line-by-Line Transaction Analysis */}
                {result.transaction_analysis && result.transaction_analysis.transactions && (
                  <div className="glass rounded-2xl p-6 border border-white/20">
                    <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-bold text-black flex items-center">
                        <FileText className="w-5 h-5 mr-3" />
                        Transaction Analysis ({result.transaction_analysis.summary.total_transactions} transactions)
                      </h3>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => handleExportReport('csv')}
                          className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
                        >
                          Export CSV
                        </button>
                        <button 
                          onClick={() => handleExportReport('pdf')}
                          className="px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors"
                        >
                          Export PDF
                        </button>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      {result.transaction_analysis.transactions.slice(0, 6).map((txn, index) => (
                        <div key={index} className="bg-white/5 rounded-lg p-4 border border-white/10">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-3">
                              <span className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                                {txn.transaction_id}
                              </span>
                              <div>
                                <div className="text-black font-medium">{txn.type}</div>
                                <div className="text-black text-sm">{txn.category}</div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-black font-semibold">₹{txn.amount.toLocaleString()}</div>
                              <div className="text-black text-sm">{txn.tax_rate} rate</div>
                            </div>
                          </div>
                          
                          <div className="mt-3 flex justify-between items-center">
                            <div className="flex gap-4">
                              <div>
                                <span className="text-black text-xs">Tax Impact:</span>
                                <span className="text-red-400 font-medium ml-1">₹{txn.tax_impact.toLocaleString()}</span>
                              </div>
                              {txn.receipt_required && (
                                <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded">
                                  Receipt Required
                                </span>
                              )}
                              {txn.deductible && (
                                <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">
                                  Deductible
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-black">
                              Formula: ₹{txn.amount.toLocaleString()} × {txn.tax_rate} = ₹{txn.tax_impact.toLocaleString()}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {result.transaction_analysis.summary.total_transactions > 6 && (
                      <div className="mt-4 text-center">
                        <p className="text-black text-sm mb-2">
                          Showing 6 of {result.transaction_analysis.summary.total_transactions} transactions
                        </p>
                        <div className="flex gap-2 justify-center">
                          <button 
                            onClick={() => handleExportReport('csv')}
                            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                          >
                            Download Complete CSV Report
                          </button>
                          <button 
                            onClick={() => handleExportReport('pdf')}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
                          >
                            Download PDF Report
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {/* Summary Stats */}
                    <div className="mt-6 grid grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-black">{result.transaction_analysis.summary.total_transactions}</div>
                        <div className="text-black text-sm">Total Transactions</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-600">₹{result.transaction_analysis.summary.total_tax_impact.toLocaleString()}</div>
                        <div className="text-black text-sm">Total Tax Impact</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-yellow-600">{result.transaction_analysis.summary.receipt_required_count}</div>
                        <div className="text-black text-sm">Receipts Needed</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{result.transaction_analysis.summary.average_tax_rate?.toFixed(1) || 0}%</div>
                        <div className="text-black text-sm">Avg Tax Rate</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Receipt Requirements */}
                {result.transaction_analysis && result.transaction_analysis.receipt_requirements && result.transaction_analysis.receipt_requirements.length > 0 && (
                  <div className="glass rounded-2xl p-6 border border-white/20">
                    <h3 className="text-lg font-bold text-black mb-4 flex items-center">
                      <Receipt className="w-5 h-5 mr-2" />
                      Receipt Requirements ({result.transaction_analysis.receipt_requirements.length})
                    </h3>
                    
                    <div className="space-y-2">
                      {result.transaction_analysis.receipt_requirements.slice(0, 6).map((req, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-yellow-500/10 rounded-lg">
                          <div>
                            <div className="text-black font-medium">Transaction #{req.transaction_id}</div>
                            <div className="text-sm text-black">{req.reason}</div>
                          </div>
                          <div className="text-yellow-600 font-semibold">₹{req.amount.toLocaleString()}</div>
                        </div>
                      ))}
                    </div>
                    
                    {result.transaction_analysis.receipt_requirements.length > 6 && (
                      <div className="mt-3 text-center">
                        <p className="text-black text-sm">
                          Showing 6 of {result.transaction_analysis.receipt_requirements.length} requirements - 
                          <button 
                            onClick={() => handleExportReport('csv')}
                            className="underline hover:text-yellow-300 ml-1"
                          >
                            download complete report
                          </button>
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Recommendations */}
                {result.recommendations && result.recommendations.length > 0 && (
                  <div className="glass rounded-2xl p-6 border border-white/20">
                    <h3 className="text-lg font-bold text-black mb-4 flex items-center">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      Tax Optimization Tips
                    </h3>
                    
                    <div className="space-y-2">
                      {result.recommendations.map((tip, index) => (
                        <div key={index} className="flex items-start">
                          <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                          <span className="text-black text-sm">{tip}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Export Buttons - Bottom */}
                <div className="glass rounded-2xl p-6 border border-white/20">
                  <h3 className="text-lg font-bold text-black mb-4 text-center">
                    Download Complete Tax Report
                  </h3>
                  <div className="flex gap-4 justify-center">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleExportReport('csv')}
                      className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <FileSpreadsheet className="w-5 h-5 mr-2" />
                      Download Excel/CSV Report
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleExportReport('pdf')}
                      className="flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      <Download className="w-5 h-5 mr-2" />
                      Download PDF Report
                    </motion.button>
                  </div>
                  <p className="text-black text-sm text-center mt-3">
                    Complete report includes all {result.transaction_analysis?.summary?.total_transactions || 0} transactions, 
                    all receipt requirements, and all tax optimization recommendations
                  </p>
                </div>
              </>
            ) : (
              <div className="glass rounded-2xl p-8 border border-white/20 text-center">
                <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">
                  Ready to Calculate
                </h3>
                <p className="text-black">
                  Enter your income details to get AI-powered tax calculations with detailed line-by-line transaction analysis
                </p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  )
}

export default TaxPage