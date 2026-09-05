# ⚡ AI-Sales-Analytics-Dashboard

A professional, modular Data Analytics web application designed for a Data Analyst portfolio. This application enables users to upload raw sales datasets (CSV / Excel), auto-inspect & clean transaction records via a FastAPI backend, store datasets in SQLite database persistence, compute multi-dimensional business analytics, explore interactive Plotly visual dashboards, scan statistical Z-score anomalies, and interact with an AI Executive Analyst for natural language briefings and Q&A.

---

## 📌 Current Architecture Pipeline

```
Upload
  ↓
Dataset Storage (SQLite + File Storage)
  ↓
Data Cleaning
  ↓
Analytics Engine
  ↓
Statistical Intelligence Engine
  ↓
AI Executive Analyst
  ↓
Frontend Dashboard
```

---

## 🚀 Phase 6 Features (Production Data Layer & Application Hardening)

- **Persistent Database Layer (`backend/database/`)**:
  - Uses SQLite with SQLAlchemy ORM (`sales_analytics.db`) for lightweight local persistence.
  - Automatically initializes schema on application startup (`init_db()`).
  - Stores metadata (`dataset_id`, `original_filename`, `upload_timestamp`, `file_size`, `file_type`, `row_count`, `column_count`, `dataset_hash`, `processing_status`, `is_active`).
- **Deterministic SHA-256 Dataset Hashing**:
  - Computes SHA-256 hash on raw file upload bytes to detect duplicate file uploads.
  - Avoids re-processing identical files and enables cross-session analytics/AI caching.
- **Unique Dataset ID Assignment**:
  - Assigns unique, URL-safe identifiers (e.g. `ds_a1b2c3d4e5f6`) to each dataset.
  - Hides internal server directory structure from API clients.
- **Dataset Management API (`backend/routes/datasets.py`)**:
  - `GET /api/datasets`: List metadata for all uploaded datasets.
  - `GET /api/datasets/{dataset_id}`: Retrieve single dataset metadata.
  - `POST /api/datasets/{dataset_id}/select`: Activate specified dataset for analysis.
  - `DELETE /api/datasets/{dataset_id}`: Safely delete physical file, database record, and invalidate related cache entries.
- **Database Caching & Invalidation (`backend/services/cache_service.py`)**:
  - Caches expensive analytics, statistical insights, AI executive summary, and AI Q&A responses per dataset hash.
  - Automatically invalidates cached entries when a dataset is changed or deleted.
- **Upload Security & Content Protection (`backend/utils/security.py`)**:
  - Configurable upload size limit (`MAX_UPLOAD_SIZE_MB=25`).
  - File extension & content parsing validation (rejects fake extensions, corrupted files, and 0-byte files).
  - Filename sanitization preventing path traversal (`../`, `..\`) and safe storage under `uploads/`.
- **API Request Validation & Standardized Errors (`backend/utils/errors.py`)**:
  - Enforces AI question length limit (`MAX_AI_QUESTION_LENGTH=1000`).
  - Standardized JSON error response format (`error`, `message`, `code`, `detail`).
  - Proper HTTP status codes: 400 (Bad Request), 404 (Not Found), 413 (File Too Large), 422 (Unprocessable Entity), 500 (Internal Error), 503 (Provider Unavailable).
- **Frontend Dataset Management (`views/data_upload.py`)**:
  - Active dataset selection dropdown and badge.
  - Uploaded datasets metadata table with real-time row/column counts and status.
  - Safe dataset deletion button with immediate UI refresh.

---

## 🔒 Phase 7A & 7B Features (Multi-Tenant Security & Zero-Cost Deployment)

- **Multi-Tenant User Isolation & JWT Security (Phase 7A)**:
  - **User Registration & Authentication (`/api/auth/register`, `/api/auth/login`)**: Bcrypt password hashing (cost factor 12) prevents plain-text storage.
  - **JWT Authorization**: Cryptographically signed JWT tokens with enforced expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
  - **Strict Server-Side Ownership Enforcements**: Every dataset query (`/api/analytics`, `/api/insights`, `/api/ai/*`, `/api/datasets/*`) strictly validates `dataset.user_id == current_user.id` on the server before execution.
  - **User-Isolated Caching & Active State**: Cache keys and active dataset selections are namespaced per `user_id`.

- **Zero-Cost Deployment Architecture (Phase 7B — ₹0 Budget)**:
  - **100% Free AI Operation (`AI_PROVIDER=none`)**: Uses `MockAIProvider` / `LocalAnalystProvider` for executive briefings and natural language data chat without paid API keys, credit cards, or external services.
  - **Free Database Compatibility**: Connection layer automatically converts legacy `postgres://` to `postgresql://` and enables pre-pinging for free tier PostgreSQL (Render, Neon, Supabase) or SQLite.
  - **Ephemeral Storage Handling (`StorageService`)**: Gracefully detects missing files after free-tier container restarts with informative 404 instructions.
  - **Dynamic URL & Host Resolution**: `BACKEND_URL` and `FRONTEND_ORIGIN` dynamically configure API calls and CORS without hardcoded `127.0.0.1` addresses.
  - **Render Free-Tier Blueprint (`render.yaml`)**: One-click deployment specification for Render free web services.

---

## 🔑 Environment Variables & Configuration

Create a `.env` file in the project root based on `.env.example`:

```env
# Application Database & Auth Security Configuration
DATABASE_URL=sqlite:///./sales_analytics.db
JWT_SECRET_KEY=your_secure_random_jwt_secret_key_at_least_32_bytes_long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Network & CORS Configuration (Render / Free Hosting Compatibility)
HOST=0.0.0.0
PORT=8000
FRONTEND_ORIGIN=http://localhost:8501
BACKEND_URL=http://127.0.0.1:8000
STORAGE_DIR=uploads

# AI Analyst Provider Configuration (Zero-Cost Mode: AI_PROVIDER=none or mock)
AI_PROVIDER=none
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Safety Limits & Controls
MAX_UPLOAD_SIZE_MB=25
MAX_AI_QUESTION_LENGTH=1000
CACHE_ENABLED=true
```

---

## 💻 How to Run the Application

### Prerequisites
- Python 3.10+ installed on your system.

### Quick Start Instructions

1. **Navigate to the project directory**:
   ```bash
   cd "AI-Sales-Analytics-Dashboard"
   ```

2. **Activate the Python virtual environment**:
   - On Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - On Windows (CMD):
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
   - On macOS / Linux:
     ```bash
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the FastAPI Backend Server** (Terminal 1):
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   *The API will be live at `http://127.0.0.1:8000` (Swagger docs at `http://127.0.0.1:8000/docs`).*

5. **Start the Streamlit Frontend App** (Terminal 2):
   ```bash
   streamlit run app.py
   ```
   *The frontend dashboard will open at `http://localhost:8501`.*

6. **Run Full Automated Test Suite**:
   ```bash
   python -m unittest tests/test_phase6.py tests/test_backend.py tests/test_analytics.py tests/test_time_series_audit.py tests/test_insights.py tests/test_ai_service.py
   ```
   *Result: 43/43 unit tests passing 100%.*

---

## 📂 Project Architecture

```
AI-Sales-Analytics-Dashboard/
├── app.py                      # Streamlit frontend entry point & controller
├── config.py                   # Theme styling, layout variables, CSS injection
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
├── .env.example                # Placeholder environment configuration
├── .gitignore                  # Git exclusion rules
├── uploads/                    # Physical dataset storage directory
├── sales_analytics.db          # SQLite persistent database file
├── backend/                    # FastAPI Backend Application
│   ├── main.py                 # FastAPI app entry point & CORS configuration
│   ├── database/
│   │   ├── __init__.py         # Database package exports
│   │   ├── connection.py       # SQLAlchemy engine & session manager
│   │   └── models.py           # DatasetRecord & CacheRecord ORM schemas
│   ├── routes/
│   │   ├── upload.py           # POST /api/upload endpoint
│   │   ├── datasets.py         # GET /api/datasets, SELECT, and DELETE endpoints
│   │   ├── analytics.py        # GET /api/analytics endpoint with caching
│   │   ├── insights.py         # GET /api/insights endpoint with caching
│   │   └── ai.py               # POST /api/ai/executive-summary & POST /api/ai/ask
│   ├── services/
│   │   ├── data_processor.py   # Ingestion, normalization & cleaning engine
│   │   ├── analytics_engine.py # Multi-dimensional BI analytics calculator
│   │   ├── insights_engine.py  # Z-score anomaly scanner & risk indicator generator
│   │   ├── ai_service.py       # OpenAI / Gemini / Mock provider abstraction
│   │   ├── dataset_service.py  # Dataset metadata, storage & activation service
│   │   ├── cache_service.py    # Analytics & AI database caching service
│   │   └── dataset_store.py    # Active dataset state manager
│   └── utils/
│       ├── security.py         # SHA-256 hashing, path traversal & content validation
│       ├── errors.py           # Global exception handlers & JSON error response helpers
│       └── validators.py       # Upload validation wrappers
├── components/                 # Reusable Streamlit UI widgets
│   ├── sidebar.py              # Sidebar navigation
│   ├── kpi_card.py             # Metric card component
│   ├── chart_card.py           # Chart container component
│   └── charts.py               # Interactive Plotly chart generators
├── views/                      # Dashboard page views
│   ├── overview.py             # Executive overview dashboard with live Plotly charts
│   ├── sales_analysis.py       # Time-series & MoM revenue deep-dive
│   ├── customer_analysis.py    # Customer spending & retention analytics
│   ├── product_analysis.py     # Product ranking & category portfolio analysis
│   ├── ai_insights.py          # AI Executive Analyst & Statistical Insights view
│   └── data_upload.py          # Dataset management & upload view
├── data/
│   ├── create_test_datasets.py # Test dataset generator script
│   └── test_datasets/          # Test files (.csv, .xlsx, empty, malformed)
└── tests/
    ├── test_backend.py         # Upload & validation test suite (Phase 2)
    ├── test_analytics.py       # Analytics & KPI test suite (Phase 3)
    ├── test_time_series_audit.py # Time series & MoM audit test suite (Phase 3)
    ├── test_insights.py        # Statistical insights & anomaly test suite (Phase 4)
    ├── test_ai_service.py      # AI service & provider abstraction test suite (Phase 5)
    └── test_phase6.py          # Production data layer & hardening test suite (Phase 6)
```

---

## 📌 Known Limitations

- **Single-Node Rate Limiting**: In-process question length & file size protections are suitable for single-node deployments. High-availability multi-instance setups would require Redis or API Gateway rate limiting.
- **SQLite Concurrency**: SQLite is optimal for single-user/development deployments. High concurrency multi-tenant workloads would benefit from PostgreSQL or MySQL.
