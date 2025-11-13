# AI Audit & Tax Assistant

A comprehensive multi-role SaaS platform for financial document processing, anomaly detection, and tax assistance using AI/ML technologies.

## 🚀 Features

### Core Capabilities
- **Multi-role Support**: Admin, Auditor, and Client roles with role-based access control
- **Document Processing**: Upload and process PDF, images, Excel, and CSV files with OCR + NLP
- **Transaction Extraction**: Automatically extract structured transaction data from documents
- **Anomaly Detection**: ML-powered fraud and anomaly detection with explainable results
- **Tax Prediction**: Predict tax liability and refunds using ML models
- **Conversational AI**: RAG-powered chatbot for document Q&A
- **Report Generation**: Generate downloadable audit and tax reports (PDF/CSV)

### Technology Stack
- **Frontend**: React 18 + TypeScript + Tailwind CSS + shadcn/ui components
- **Backend**: Python FastAPI + MongoDB + JWT authentication
- **ML/AI**: scikit-learn, XGBoost, sentence-transformers, FAISS, OpenAI API
- **Document Processing**: Tesseract OCR, pdfplumber, spaCy NLP
- **State Management**: Zustand + React Query

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 5.0+
- Redis (for background tasks)
- Tesseract OCR

## 🛠️ Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd ai-audit-tax-assistant
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your configuration
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Database Setup
```bash
# Start MongoDB
mongod

# The application will create indexes automatically on first run
```

### 5. Train ML Models
```bash
cd ml_models

# Train anomaly detection model
python train_anomaly_model.py --create_sample

# Train tax prediction model
python train_tax_model.py --create_sample
```

## 🚀 Running the Application

### Start Backend
```bash
cd backend
python main.py
# API will be available at http://localhost:8000
```

### Start Frontend
```bash
cd frontend
npm run dev
# Frontend will be available at http://localhost:3000
```

## 📁 Project Structure

```
ai-audit-tax-assistant/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Configuration & security
│   │   ├── models/        # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utilities
│   └── main.py           # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── stores/        # State management
│   │   └── types/         # TypeScript types
│   └── package.json
├── ml_models/            # ML training scripts
├── data/                 # Sample data & training sets
└── requirements.txt      # Python dependencies
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_audit_tax_db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_BUCKET_NAME=ai-audit-documents
AWS_REGION=us-east-1

# LLM API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# OCR Services (Optional)
GOOGLE_VISION_API_KEY=your-google-vision-key
AWS_TEXTRACT_REGION=us-east-1

# Redis
REDIS_URL=redis://localhost:6379/0
```

## 🎯 User Flows

### 1. Authentication & Onboarding
- Sign up with role selection (admin/auditor/client)
- Email verification (optional)
- Role-based dashboard redirection

### 2. Document Upload & Processing
- Drag-and-drop file upload
- Real-time processing status
- Manual correction interface for extracted data

### 3. Audit Workflow
- Select client and documents for audit
- Run anomaly detection
- Review flagged transactions with explanations
- Resolve anomalies with notes

### 4. Tax Calculation
- Input income and deduction details
- Get ML-powered tax predictions
- View breakdown with explainability
- Generate tax reports

### 5. AI Chatbot
- Ask questions about uploaded documents
- Get answers with source citations
- Pin documents for persistent context
- Save answers as reports

## 🤖 ML Models

### Anomaly Detection Model
- **Algorithm**: Isolation Forest
- **Features**: Amount patterns, merchant frequency, time-based features
- **Output**: Anomaly score (0-1) with explanations
- **Training**: `python ml_models/train_anomaly_model.py`

### Tax Prediction Model
- **Algorithm**: XGBoost Regressor
- **Features**: Income types, deductions, historical patterns
- **Output**: Tax liability with confidence and explainability
- **Training**: `python ml_models/train_tax_model.py`

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user profile

### Documents
- `POST /api/documents/upload` - Upload document
- `POST /api/documents/{id}/process` - Process document
- `GET /api/documents/{id}` - Get document details
- `PATCH /api/documents/{id}/parsed` - Update parsed data

### Transactions
- `GET /api/transactions` - List transactions with filters
- `GET /api/transactions/{id}` - Get transaction details
- `PATCH /api/transactions/{id}` - Update transaction

### Audit
- `POST /api/audit/scan` - Run anomaly detection
- `GET /api/audit/{id}/anomalies` - Get audit results
- `POST /api/audit/{id}/resolve` - Resolve anomaly

### Tax
- `POST /api/tax/predict` - Predict tax liability
- `GET /api/tax/records` - List tax records
- `GET /api/tax/slabs/{year}` - Get tax slabs

### Chatbot
- `POST /api/chatbot/message` - Send message to AI
- `GET /api/chatbot/conversations` - Get chat history
- `POST /api/chatbot/pin-document` - Pin document for context

### Reports
- `POST /api/reports/generate` - Generate report
- `GET /api/reports/{id}/download` - Download report
- `GET /api/reports` - List reports

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Docker Deployment (TODO)
```bash
docker-compose up -d
```

### Manual Deployment
1. Set up production environment variables
2. Configure MongoDB and Redis
3. Build frontend: `npm run build`
4. Deploy backend with gunicorn/uvicorn
5. Set up reverse proxy (nginx)
6. Configure SSL certificates

## 🔒 Security Considerations

- JWT-based authentication with role-based access control
- Input validation and sanitization
- Rate limiting on API endpoints
- Secure file upload with type validation
- PII data handling compliance
- Audit logging for sensitive operations

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 TODO Items

### High Priority
- [ ] Implement file storage (S3/local)
- [ ] Add Celery for background processing
- [ ] Implement email notifications
- [ ] Add comprehensive error handling
- [ ] Create Docker configuration
- [ ] Add API rate limiting

### ML/AI Enhancements
- [ ] Fine-tune NER models for financial documents
- [ ] Implement SHAP explainability
- [ ] Add model monitoring and drift detection
- [ ] Create model retraining pipelines
- [ ] Implement ensemble methods

### Frontend Enhancements
- [ ] Add data visualization charts
- [ ] Implement real-time notifications
- [ ] Add dark mode support
- [ ] Create mobile-responsive design
- [ ] Add accessibility features

### Security & Compliance
- [ ] Implement audit logging
- [ ] Add data encryption at rest
- [ ] Create backup and recovery procedures
- [ ] Add compliance reporting features
- [ ] Implement user activity monitoring

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API documentation at `/docs` when running the backend

## 🙏 Acknowledgments

- OpenAI for GPT models
- Hugging Face for transformer models
- FastAPI for the excellent web framework
- React and the amazing ecosystem
- All open-source contributors