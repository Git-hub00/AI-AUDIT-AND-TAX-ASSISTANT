import React, { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  MessageSquare, 
  Send, 
  Upload, 
  Bot, 
  User,
  FileText,
  Paperclip,
  Sparkles,
  Mic,
  MicOff,
  Volume2,
  Download,
  CheckCircle
} from 'lucide-react'
import { api } from '../services/api'
import { useVoiceRecognition } from '../hooks/useVoiceRecognition'

interface Message {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
  preview?: any[]
  files?: any[]
  sessionId?: string
}

const ChatbotPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: 'Hello! I\'m your CSV Processing Assistant. Upload a bank statement or transaction CSV file, and I\'ll help you filter and analyze the data.\n\nTry commands like:\n• "Show only credit transactions"\n• "List debits above ₹2000"\n• "Give credits and debits separately"',
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { isListening, transcript, startListening, stopListening, resetTranscript, isSupported } = useVoiceRecognition()

  useEffect(() => {
    if (transcript) {
      setInputMessage(transcript)
    }
  }, [transcript])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const file = e.target.files[0]
      if (file && file.name.endsWith('.csv')) {
        setFiles([file])
      } else {
        alert('Please select a CSV file')
      }
    }
  }

  const handleGenerateFiles = async (sessionId: string) => {
    try {
      setLoading(true)
      const response = await api.post('/chatbot/generate-files', {
        session_id: sessionId
      })
      
      if (response.data.success) {
        const botResponse: Message = {
          id: Date.now().toString(),
          type: 'bot',
          content: response.data.message,
          timestamp: new Date(),
          files: response.data.files,
          sessionId: sessionId
        }
        setMessages(prev => [...prev, botResponse])
      }
    } catch (error) {
      console.error('Error generating files:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadFile = async (sessionId: string, filename: string) => {
    try {
      const response = await api.get(`/chatbot/download/${sessionId}/${filename}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading file:', error)
    }
  }

  const handleSendMessage = async (useVoice: boolean = false) => {
    if (!inputMessage.trim() && files.length === 0) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage || `Uploaded ${files.length} file(s)`,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const messageToSend = inputMessage
    setInputMessage('')
    resetTranscript()
    setLoading(true)

    try {
      let response
      
      // Handle file upload
      if (files.length > 0) {
        const formData = new FormData()
        formData.append('file', files[0])
        
        response = await api.post('/chatbot/upload-csv', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        if (response.data.success) {
          setCurrentSessionId(response.data.session_id)
        }
      } else if (currentSessionId && messageToSend) {
        // Process command with existing session
        response = await api.post('/chatbot/process-command', {
          session_id: currentSessionId,
          command: messageToSend
        })
      } else {
        // General chat
        response = await api.post('/chatbot/csv-chat', {
          message: messageToSend,
          voice: useVoice
        })
      }

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.data.message || response.data.response,
        timestamp: new Date(),
        preview: response.data.preview,
        files: response.data.files,
        sessionId: response.data.session_id || currentSessionId
      }
      
      setMessages(prev => [...prev, botResponse])
      
    } catch (error: any) {
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorResponse])
    } finally {
      setFiles([])
      setLoading(false)
    }
  }

  const handleVoiceMessage = () => {
    if (isListening) {
      stopListening()
      if (transcript) {
        handleSendMessage(true)
      }
    } else {
      startListening()
    }
  }

  const speakMessage = (content: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(content)
      utterance.rate = 0.9
      speechSynthesis.speak(utterance)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">

      <div className="relative z-10 max-w-4xl mx-auto h-full">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-6"
        >
          <div className="flex items-center mb-4">
            <div className="p-3 bg-gradient-to-r from-green-600 to-green-800 rounded-2xl mr-4">
              <MessageSquare className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">CSV Processing Assistant</h1>
              <p className="text-gray-600 text-lg">Upload & filter bank statements with voice commands</p>
            </div>
          </div>
        </motion.div>

        {/* Chat Container */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-white rounded-2xl border border-gray-200 shadow-sm h-[calc(100vh-200px)] flex flex-col"
        >
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  {/* Avatar */}
                  <div className={`flex-shrink-0 ${message.type === 'user' ? 'ml-3' : 'mr-3'}`}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      message.type === 'user' 
                        ? 'bg-gradient-to-r from-gray-600 to-gray-800' 
                        : 'bg-gradient-to-r from-green-600 to-green-800'
                    }`}>
                      {message.type === 'user' ? (
                        <User className="w-5 h-5 text-white" />
                      ) : (
                        <Bot className="w-5 h-5 text-white" />
                      )}
                    </div>
                  </div>

                  {/* Message Content */}
                  <div className={`rounded-2xl px-4 py-3 ${
                    message.type === 'user'
                      ? 'bg-gradient-to-r from-gray-600 to-gray-800 text-white'
                      : 'bg-gray-50 text-gray-900 border border-gray-200'
                  }`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                    
                    {/* Preview Data */}
                    {message.preview && message.preview.length > 0 && (
                      <div className="mt-3 p-3 bg-gray-100 rounded-lg">
                        <h4 className="text-xs font-semibold text-gray-600 mb-2">Preview:</h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="border-b border-gray-200">
                                {Object.keys(message.preview[0]).map(key => (
                                  <th key={key} className="text-left p-1 text-gray-600">{key}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {message.preview.map((row, idx) => (
                                <tr key={idx} className="border-b border-gray-100">
                                  {Object.values(row).map((value: any, vidx) => (
                                    <td key={vidx} className="p-1 text-gray-700">
                                      {value?.toString() || 'N/A'}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        {message.sessionId && (
                          <button
                            onClick={() => handleGenerateFiles(message.sessionId!)}
                            className="mt-2 px-3 py-1 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200"
                          >
                            <CheckCircle className="w-3 h-3 inline mr-1" />
                            Generate Files
                          </button>
                        )}
                      </div>
                    )}
                    
                    {/* Download Files */}
                    {message.files && message.files.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {message.files.map((file, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleDownloadFile(message.sessionId!, file.filename)}
                            className="flex items-center px-3 py-2 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200 w-full"
                          >
                            <Download className="w-3 h-3 mr-2" />
                            Download {file.filename} ({file.size} bytes)
                          </button>
                        ))}
                      </div>
                    )}
                    
                    {message.type === 'bot' && (
                      <button
                        onClick={() => speakMessage(message.content)}
                        className="mt-2 text-xs text-gray-500 hover:text-gray-700 flex items-center"
                      >
                        <Volume2 className="w-3 h-3 mr-1" />
                        Speak
                      </button>
                    )}
                    <p className={`text-xs mt-2 ${
                      message.type === 'user' ? 'text-gray-200' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}

            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="flex mr-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* File Upload Area */}
          {files.length > 0 && (
            <div className="px-6 py-3 border-t border-gray-200">
              <div className="flex flex-wrap gap-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center bg-gray-100 rounded-lg px-3 py-2 text-sm text-gray-700">
                    <FileText className="w-4 h-4 mr-2" />
                    <span>{file.name}</span>
                    <button
                      onClick={() => setFiles(prev => prev.filter((_, i) => i !== index))}
                      className="ml-2 text-gray-500 hover:text-gray-700"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="p-6 border-t border-gray-200">
            <div className="flex items-end space-x-4">
              {/* Voice and File Upload Buttons */}
              <div className="flex-shrink-0 flex space-x-2">
                {isSupported && (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleVoiceMessage}
                    className={`p-3 rounded-xl transition-colors ${
                      isListening 
                        ? 'bg-red-500 text-white' 
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                    }`}
                  >
                    {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                  </motion.button>
                )}
                
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="chat-file-upload"
                  accept=".csv"
                />
                <label htmlFor="chat-file-upload">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-3 bg-gray-100 hover:bg-gray-200 rounded-xl cursor-pointer transition-colors"
                  >
                    <Paperclip className="w-5 h-5 text-gray-600" />
                  </motion.div>
                </label>
              </div>

              {/* Message Input */}
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Upload CSV and ask: 'Show credits above ₹5000' or 'Separate credits and debits'..."
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                  rows={1}
                />
              </div>

              {/* Send Button */}
              <div className="flex-shrink-0">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleSendMessage(false)}
                  disabled={loading || (!inputMessage.trim() && files.length === 0)}
                  className="p-3 bg-gradient-to-r from-green-600 to-green-800 hover:from-green-700 hover:to-green-900 rounded-xl text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <Send className="w-5 h-5" />
                </motion.button>
              </div>
            </div>

            {/* Voice Status and Quick Actions */}
            {isListening && (
              <div className="mt-2 text-center">
                <p className="text-sm text-red-300 animate-pulse">🎤 Listening... Speak your question</p>
              </div>
            )}
            
            <div className="mt-4 flex flex-wrap gap-2">
              {[
                'Show only credit transactions',
                'List debits above ₹2000',
                'Give credits and debits separately',
                'Show transactions from last month',
                'Filter by amount range'
              ].map((suggestion, index) => (
                <motion.button
                  key={index}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setInputMessage(suggestion)}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800 rounded-full transition-colors flex items-center"
                >
                  <Sparkles className="w-3 h-3 mr-1" />
                  {suggestion}
                </motion.button>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default ChatbotPage