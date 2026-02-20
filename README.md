# KommandAI

**Agentic AI Command & Control System** - A multi-vendor marketplace platform powered by natural language commands using Google Gemini AI.

## Screenshots

| Dashboard | Light Mode |
|-----------|------------|
| ![](assets/Dashboard.png) | ![](assets/LightMode.png) |

| AI Search | Shops |
|-----------|-------|
| ![](assets/SearchNLP.png) | ![](assets/Shops.png) |

## Features

- **Natural Language Commands**: Control the entire platform using Hindi/English voice or text
- **Multi-Vendor Marketplace**: Multiple shops, products, orders, and customers
- **Role-Based Access**: Super Admin, Shop Admin, and Customer dashboards
- **AI-Powered Search**: Smart product search and command suggestions
- **Real-time Updates**: WebSocket-based live notifications
- **Profit Tracking**: Cost price, MRP, selling price, and profit calculations
- **Voice Support**: Speak commands in Hindi or English

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Frontend | React + Vite |
| Database | PostgreSQL |
| AI | Google Gemini 2.5 Flash |
| Real-time | WebSockets |

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Google Gemini API Key ([Get it here](https://makersuite.google.com/app/apikey))

### 1. Clone & Setup Backend

```bash
# Clone the repository
git clone https://github.com/gaurav9479/AgentSamosa.git
cd AgentSamosa

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values:
DATABASE_URL=postgresql://user:password@localhost:5432/kommandai
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb kommandai

# Or using psql
psql -c "CREATE DATABASE kommandai;"
```

### 4. Run Backend

```bash
# From project root
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 5. Setup & Run Frontend

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:3000

### 6. Default Accounts

On first startup, these accounts are created automatically:

| Role | Email | Password |
|------|-------|----------|
| Super Admin | `superadmin@kommandai.com` | `qwert12345` |
| Shop Admin | `admin@kommandai.com` | `qwert12345` |
| Customer | `customer@kommandai.com` | `qwert12345` |

---

## Deployment Guide

### Backend Deployment (Render)

1. **Create Render Account**: Go to [render.com](https://render.com) and sign up

2. **Create PostgreSQL Database**:
   - Dashboard → New → PostgreSQL
   - Name: `kommandai-db`
   - Copy the **Internal Database URL**

3. **Deploy Backend**:
   - Dashboard → New → Web Service
   - Connect your GitHub repository
   - Configure:
     - **Name**: `kommandai-api`
     - **Root Directory**: (leave empty)
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**:
   - `DATABASE_URL` = Your Render PostgreSQL Internal URL
   - `GEMINI_API_KEY` = Your Google Gemini API key

5. **Deploy** - Your backend will be at: `https://kommandai-api.onrender.com`

### Frontend Deployment (Vercel)

1. **Create Vercel Account**: Go to [vercel.com](https://vercel.com) and sign up

2. **Import Project**:
   - New Project → Import Git Repository
   - Select your repository
   - Configure:
     - **Root Directory**: `frontend`
     - **Framework Preset**: Vite

3. **Add Environment Variables**:
   - `VITE_API_URL` = `https://your-backend-url.onrender.com` (your Render backend URL)
   - `VITE_WS_URL` = `wss://your-backend-url.onrender.com` (same URL with wss://)

4. **Deploy** - Your frontend will be at: `https://your-app.vercel.app`

### Alternative: Frontend on Netlify

1. **Create Netlify Account**: Go to [netlify.com](https://netlify.com)

2. **Import Project**:
   - Add new site → Import from Git
   - Select repository
   - Configure:
     - **Base directory**: `frontend`
     - **Build command**: `npm run build`
     - **Publish directory**: `frontend/dist`

3. **Add Environment Variables** (Site settings → Environment variables):
   - `VITE_API_URL` = Your backend URL
   - `VITE_WS_URL` = Your WebSocket URL (wss://...)

4. **Add Redirects**: Create `frontend/public/_redirects`:
   ```
   /* /index.html 200
   ```

### Alternative: Full Stack on Railway

1. **Create Railway Account**: Go to [railway.app](https://railway.app)

2. **Create New Project** → Deploy from GitHub repo

3. **Add PostgreSQL**:
   - Click "+ New" → Database → PostgreSQL
   - Railway auto-connects it

4. **Configure Backend Service**:
   - Settings → Variables:
     - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
     - `GEMINI_API_KEY` = Your Gemini key
   - Settings → Deploy:
     - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Add Frontend Service**:
   - Click "+ New" → GitHub Repo (same repo)
   - Set Root Directory: `frontend`
   - Add Variables:
     - `VITE_API_URL` = Backend service URL
     - `VITE_WS_URL` = Backend WebSocket URL

---

## Architecture

```
User Command (Voice/Text)
        ↓
   [Frontend React App]
        ↓
   [FastAPI Backend]
        ↓
   [Gemini AI - Intent Parser]
        ↓
   [Action Executor]
        ↓
   [PostgreSQL Database]
        ↓
   [WebSocket Broadcast]
        ↓
   [Real-time UI Update]
```

## API Endpoints

### Main Command Endpoint

```bash
POST /api/command
{
  "text": "show pending orders",
  "context": {
    "user_email": "admin@kommandai.com",
    "user_role": "admin",
    "shop_id": 1
  }
}
```

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List products |
| GET | `/api/shops` | List shops |
| GET | `/api/orders` | List orders |
| GET | `/api/shop-categories` | List categories |
| POST | `/api/command` | Execute AI command |
| GET | `/api/health` | Health check |
| WS | `/api/ws` | WebSocket connection |

## Example Commands

### Super Admin
- "show platform stats"
- "list all shops"
- "verify shop 5"
- "show pending shops"

### Shop Admin
- "show dashboard"
- "list products"
- "show pending orders"
- "add product iPhone price 99999"

### Customer
- "search lipstick"
- "show my orders"
- "meri orders dikhao" (Hindi)

## Project Structure

```
KommandAI/
├── app/
│   ├── api/routes.py          # API endpoints
│   ├── core/
│   │   ├── config.py          # Settings
│   │   ├── database.py        # PostgreSQL connection
│   │   └── websocket.py       # WebSocket manager
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── services/
│   │   ├── intent_parser.py   # Gemini AI integration
│   │   ├── action_executor.py # Command execution
│   │   └── *_service.py       # Business logic
│   └── main.py                # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main React app
│   │   ├── config.js          # API configuration
│   │   └── index.css          # Styles
│   ├── vercel.json            # Vercel config
│   └── package.json
├── requirements.txt
├── Procfile                   # Render deployment
├── runtime.txt               # Python version
└── README.md
```

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
GEMINI_API_KEY=your_gemini_api_key
```

### Frontend (Vercel/Netlify)

```env
VITE_API_URL=https://your-backend.onrender.com
VITE_WS_URL=wss://your-backend.onrender.com
```

## Troubleshooting

### Backend not starting?
- Check PostgreSQL is running
- Verify DATABASE_URL format
- Ensure GEMINI_API_KEY is valid

### Frontend can't connect to backend?
- Check VITE_API_URL is set correctly
- Ensure backend CORS allows your frontend domain
- For WebSocket, use `wss://` for HTTPS sites

### Render free tier sleeping?
- Free tier sleeps after 15 min of inactivity
- First request after sleep takes ~30 seconds
- Consider upgrading for production use

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
