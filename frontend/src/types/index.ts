// User and Auth Types
export interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'auditor' | 'client'
  created_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  name: string
  email: string
  password: string
  role: 'admin' | 'auditor' | 'client'
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token?: string
}

// Document Types
export interface Document {
  id: string
  user_id: string
  client_id?: string
  filename: string
  storage_path: string
  type: 'invoice' | 'receipt' | 'statement' | 'bank'
  status: 'uploaded' | 'processing' | 'done' | 'error'
  parsed_data?: ParsedData
  ocr_confidence?: number
  uploaded_at: string
  meta?: {
    pages?: number
    size_bytes?: number
    content_type?: string
  }
}

export interface ParsedData {
  transactions: Transaction[]
  raw_text: string
  tables: any[]
}

export interface Transaction {
  id: string
  date: string
  description: string
  merchant: string
  category: string
  amount: number
  currency: string
  source_coords?: any
}

// Transaction Database Types
export interface TransactionDB {
  id: string
  document_id: string
  client_id: string
  user_id: string
  date: string
  amount: number
  currency: string
  description: string
  merchant: string
  category: string
  anomaly_score?: number
  anomaly_reasons: Array<{rule: string, detail: string}>
  created_at: string
}

// Audit Types
export interface Anomaly {
  txn_id: string
  score: number
  reason: string
  evidence: {
    amount?: number
    merchant?: string
    [key: string]: any
  }
}

// Tax Types
export interface TaxPrediction {
  tax_record_id: string
  predicted_tax: number
  breakdown: {
    taxable_income: number
    slab_details: Array<{
      slab_range: string
      rate: string
      taxable_amount: number
      tax_amount: number
    }>
    credits: number
    total_deductions: number
  }
  confidence: number
  explainability: {
    top_features: Array<{
      feature: string
      impact: number
      value?: number
      description?: string
    }>
  }
  income_breakdown?: {
    total_income: number
    by_category: Record<string, number>
    transaction_count: number
  }
}

export interface TaxRecord {
  id: string
  user_id: string
  fiscal_year: string
  predicted_tax: number
  breakdown: TaxPrediction['breakdown']
  confidence: number
  status: 'predicted' | 'filed'
  filing_id?: string
  created_at: string
  filed_at?: string
}

// Chatbot Types
export interface ChatMessage {
  user_id: string
  message: string
  context_doc_ids?: string[]
  max_tokens?: number
}

export interface ChatResponse {
  reply: string
  sources: Array<{
    doc_id: string
    title: string
    snippet: string
    score?: number
  }>
  metadata: {
    retrieval_docs?: number
    context_length?: number
    model?: string
    error?: string
  }
}

export interface Conversation {
  id: string
  user_id: string
  message: string
  response: string
  sources: ChatResponse['sources']
  context_doc_ids: string[]
  metadata: ChatResponse['metadata']
  created_at: string
}



// API Response Types
export interface ApiResponse<T> {
  data?: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_next?: boolean
  has_prev?: boolean
}

// Component Props Types
export interface FileUploaderProps {
  acceptedTypes: string[]
  maxSizeMB?: number
  onComplete: (fileMeta: any) => void
  multiple?: boolean
  disabled?: boolean
}

export interface DocumentParserPanelProps {
  documentId: string
  onSave?: (parsedData: ParsedData) => void
}

export interface TransactionTableProps {
  clientId?: string
  filters?: {
    date_from?: string
    date_to?: string
    merchant?: string
    category?: string
    min_amount?: number
    max_amount?: number
  }
  pageSize?: number
  onRowClick?: (transaction: TransactionDB) => void
}

export interface AnomalyListProps {
  anomalies: Anomaly[]
  onResolve?: (anomalyId: string, note: string) => void
  onExplain?: (anomaly: Anomaly) => void
}

export interface TaxCalculatorProps {
  onCalculate?: (prediction: TaxPrediction) => void
}

export interface ChatbotProps {
  pinnedDocIds?: string[]
  onPinDocument?: (docId: string) => void
  onUnpinDocument?: (docId: string) => void
}



// Filter and Search Types
export interface TransactionFilters {
  client_id?: string
  date_from?: string
  date_to?: string
  merchant?: string
  category?: string
  min_amount?: number
  max_amount?: number
  sort_by?: 'date' | 'amount' | 'anomaly_score'
  sort_order?: 'asc' | 'desc'
}

export interface DocumentFilters {
  client_id?: string
  status?: Document['status']
  type?: Document['type']
  search?: string
}

// Form Types
export interface UploadFormData {
  files: File[]
  client_id?: string
  type: Document['type']
}

export interface TaxCalculationFormData {
  fiscal_year: string
  income_types: {
    salary?: number
    business?: number
    capital_gains?: number
    interest?: number
    rental?: number
    other?: number
  }
  deductions: {
    standard_deduction?: number
    hra_exemption?: number
    section_80c?: number
    section_80d?: number
    other?: number
  }
}

// Error Types
export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: any
}