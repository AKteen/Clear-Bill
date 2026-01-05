# Document Processor - AI-Powered Invoice Analysis & Audit System

A production-ready document processing application that combines AI analysis with automated audit compliance checking. Upload PDFs and images to get instant AI-powered analysis with comprehensive policy validation and duplicate detection.

<img width="1949" height="1331" alt="Clearbill-img" src="https://github.com/user-attachments/assets/17161ce4-8d09-4966-8bcb-dabc05178801" />



## 🚀 Features

### Core Functionality
- **AI Document Analysis** - Powered by Groq's Llama models for text and vision processing
- **Invoice-Only Processing** - Automatically filters and rejects non-invoice documents
- **Automated Audit System** - Configurable policy engine with compliance scoring
- **Duplicate Detection** - SHA-256 hashing prevents reprocessing of identical documents
- **Multi-Format Support** - Handles PDFs, images (PNG, JPG, GIF, BMP, TIFF)
- **Cloud Storage** - Automatic file backup to Cloudinary (compliant documents only)

### Audit & Compliance
- **Policy Engine** - Customizable rules for invoice validation
- **Content Warnings** - Flags alcohol, entertainment, luxury items, high-risk vendors
- **Compliance Scoring** - Real-time compliance percentage calculation
- **Violation Tracking** - Detailed reporting of policy violations with severity levels

### User Experience
- **Modern Dark UI** - Sleek interface with orange-red accent colors
- **Chat Interface** - Conversational document processing experience
- **Document History** - Sidebar with clickable document archive
- **Real-time Processing** - Parallel upload and AI analysis
- **Drag & Drop** - Intuitive file upload with visual feedback

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Neon serverless database with connection pooling
- **SQLAlchemy** - ORM with automatic migrations
- **Groq API** - AI models (Llama-3.3-70b-versatile, meta-llama/llama-4-scout-17b-16e-instruct)
- **PyMuPDF** - PDF processing and text extraction
- **Cloudinary** - Cloud file storage and CDN

### Frontend
- **React 19** - Modern UI framework
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling with custom dark theme
- **Axios** - HTTP client for API communication

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database (Neon recommended)
- Groq API key
- Cloudinary account

## 🚀 Quick Start

### Backend Setup

1. **Clone and navigate to backend**
   ```bash
   cd backend
   python -m venv myenv
   myenv\Scripts\activate  # Windows
   # source myenv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Environment Variables**
   ```env
   DATABASE_URL=postgresql://user:pass@host:port/db
   GROQ_API_KEY=your_groq_api_key
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   SECRET_KEY=your_secret_key
   MAX_FILE_SIZE=10485760
   ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg,gif,bmp,tiff
   ```

5. **Run backend**
   ```bash
   python main.py
   ```

### Frontend Setup

1. **Navigate to frontend**
   ```bash
   cd frontend/frontapp
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Access application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📊 Audit Policies

The system includes pre-configured audit policies:

### Required Fields
- Invoice Number
- Amount
- Date  
- Vendor Name

### Validation Rules
- Amount limits ($1 - $10,000)
- Invoice number format validation
- Date range checking (within 365 days)

### Content Warnings
- **Alcohol**: beer, wine, liquor, etc.
- **Entertainment**: parties, clubs, casinos
- **High-Risk**: cash only, no receipt, off books
- **Luxury Items**: jewelry, designer brands

## 🔧 API Endpoints

### Core Endpoints
- `POST /upload` - Upload and process documents
- `GET /document/{id}` - Retrieve processed document
- `GET /audit-policies` - View audit configuration
- `GET /health` - System health check

### Response Format
```json
{
  "success": true,
  "message": "Document processed successfully",
  "data": {
    "id": 1,
    "file_hash": "abc123...",
    "file_type": "image",
    "original_filename": "invoice.pdf",
    "cloudinary_url": "https://res.cloudinary.com/...",
    "groq_response": "AI analysis...",
    "audit_result": {
      "is_compliant": true,
      "compliance_score": 85.5,
      "violations": [],
      "summary": "Document compliant"
    }
  }
}
```

## 🏗️ Architecture

### Database Schema
- **documents** - File metadata, hashes, AI responses, audit results
- **audit_policies** - Configurable validation rules with severity levels

### Processing Flow
1. File upload with validation
2. Duplicate detection via SHA-256 hashing
3. Groq AI analysis to determine document type
4. Invoice format validation (rejects non-invoices)
5. Cloudinary upload (only for valid invoices)
6. Audit policy validation with compliance scoring
7. Database storage (only for compliant documents)

### Security Features
- File type validation
- Size limits (10MB default)
- Invoice format validation (rejects non-invoices)
- Restricted item detection (alcohol, entertainment, luxury)
- SQL injection prevention
- Environment variable configuration
- Secure hash generation with salt
- Database storage only for compliant documents

## 🚀 Deployment

### Backend Deployment
```bash
# Production server
uvicorn main:app --host 0.0.0.0 --port 8000

# With SSL and workers
uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem --workers 4
```

### Frontend Deployment
```bash
npm run build
# Deploy dist/ folder to your hosting service
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request



## 🙏 Acknowledgments

- [Groq](https://groq.com/) for AI model APIs
- [Cloudinary](https://cloudinary.com/) for cloud storage
- [Neon](https://neon.tech/) for serverless PostgreSQL
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
