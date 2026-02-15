# 🚀 Deployment Guide - AlgoTradeX

## Free Hosting Options

### Option 1: Railway.app (RECOMMENDED)
**Cost:** FREE (500 hours/month)  
**Best for:** Backend + Database

#### Deploy Backend + Database to Railway

1. **Sign up**: Go to [railway.app](https://railway.app) and sign up with GitHub

2. **Create New Project**:
   ```
   - Click "New Project"
   - Select "Deploy PostgreSQL"
   - Note the connection string
   ```

3. **Deploy FastAPI Backend**:
   ```
   - Click "New Service" → "GitHub Repo"
   - Select your algotrader repository
   - Railway auto-detects Python
   - Set root directory: `backend`
   ```

4. **Configure Environment Variables** (in Railway dashboard):
   ```
   DATABASE_URL=<your-postgresql-connection-string>
   DEBUG=False
   CORS_ORIGINS=https://*.streamlit.app
   ```

5. **Add Start Command**:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

6. **Deploy**: Railway will auto-deploy. Note your backend URL (e.g., `https://yourapp.railway.app`)

---

### Option 2: Render.com
**Cost:** FREE  
**Best for:** Backend

#### Deploy Backend to Render

1. **Sign up**: [render.com](https://render.com)

2. **Create Web Service**:
   ```
   - New → Web Service
   - Connect GitHub repo
   - Root Directory: backend
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Add PostgreSQL Database**:
   ```
   - New → PostgreSQL
   - Copy Internal Database URL
   ```

4. **Environment Variables**:
   ```
   DATABASE_URL=<internal-database-url>
   CORS_ORIGINS=https://*.streamlit.app
   ```

5. **Deploy**: Auto-deploys on git push

---

### Option 3: Streamlit Cloud (Frontend)
**Cost:** FREE (unlimited public apps)  
**Best for:** Frontend

#### Deploy Streamlit Dashboard

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Deploy**:
   ```
   - Sign in with GitHub
   - Click "New app"
   - Repository: your-repo
   - Branch: main
   - Main file path: frontend/streamlit_app.py
   ```

4. **Configure**:
   - Add secrets in Streamlit Cloud settings:
     ```toml
     [api]
     url = "https://your-backend.railway.app/api/v1"
     ```

5. **Update Code**:
   ```python
   # In streamlit_app.py
   import streamlit as st
   
   API_URL = st.secrets.get("api", {}).get("url", "http://localhost:8000/api/v1")
   ```

6. **Deploy**: App will be live at `https://your-app.streamlit.app`

---

## Database Setup (PostgreSQL)

### Option 1: Supabase (Recommended)
**Cost:** FREE (500MB storage)  
**Includes:** PostgreSQL + TimescaleDB extension

1. Sign up at [supabase.com](https://supabase.com)

2. Create new project

3. Enable TimescaleDB:
   ```sql
   -- Go to SQL Editor in Supabase dashboard
   CREATE EXTENSION IF NOT EXISTS timescaledb;
   ```

4. Get connection string:
   ```
   Settings → Database → Connection string
   ```

5. Update your backend `.env`:
   ```
   DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
   ```

---

### Option 2: Railway PostgreSQL
**Cost:** FREE  
**Included with Railway backend**

1. Already created when you deployed backend above

2. Connection string is auto-injected as `DATABASE_URL`

3. Enable TimescaleDB:
   ```bash
   # Connect to Railway PostgreSQL
   railway run psql $DATABASE_URL
   
   # In psql:
   CREATE EXTENSION IF NOT EXISTS timescaledb;
   ```

---

### Option 3: ElephantSQL
**Cost:** FREE (20MB - enough for MVP)

1. Sign up at [elephantsql.com](https://elephantsql.com)

2. Create new instance (Tiny Turtle plan - FREE)

3. Copy connection URL

---

## Complete Deployment Flow

### Step 1: Prepare Code

```bash
# 1. Create .env file
cp .env.example .env

# Edit .env with production values:
DATABASE_URL=<your-production-db-url>
DEBUG=False
CORS_ORIGINS=https://*.streamlit.app

# 2. Commit to GitHub
git add .
git commit -m "Production ready"
git push origin main
```

---

### Step 2: Deploy Backend (Railway)

```bash
# Railway CLI (optional, for faster deployment)
npm install -g @railway/cli
railway login
railway init
railway up
```

OR use Railway web dashboard as described above.

---

### Step 3: Initialize Database

```bash
# Option A: Local init then export
python scripts/init_db.py  # Run locally
pg_dump algotrader > backup.sql
psql $PRODUCTION_DATABASE_URL < backup.sql

# Option B: Run init script on production
railway run python scripts/init_db.py
```

---

### Step 4: Deploy Frontend (Streamlit Cloud)

1. Push to GitHub (done above)
2. Go to share.streamlit.io
3. Deploy from repo
4. Done! ✅

---

## Post-Deployment Checklist

### ✅ Backend Health Check

```bash
# Test API is live
curl https://your-backend.railway.app/health

# Expected response:
{
  "status": "healthy",
  "database": "connected"
}
```

### ✅ Database Verification

```sql
-- Connect to production DB
psql $DATABASE_URL

-- Check tables exist
\dt

-- Check TimescaleDB is enabled
SELECT * FROM timescaledb_information.hypertables;

-- Verify data
SELECT COUNT(*) FROM stocks;
SELECT COUNT(*) FROM ohlcv_data;
```

### ✅ Frontend Check

1. Open your Streamlit app URL
2. Check backend connection in sidebar (should show "✅ Backend Online")
3. Try running a backtest
4. Verify results display correctly

---

## Environment Variables Reference

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# App Config
DEBUG=False
APP_NAME=AlgoTradeX
APP_VERSION=1.0.0

# CORS (important for Streamlit frontend)
CORS_ORIGINS=https://*.streamlit.app,https://your-custom-domain.com

# Trading
DEFAULT_INITIAL_CAPITAL=100000.0
TRANSACTION_COST_PERCENT=0.05

# Data Fetching
YFINANCE_DELAY=1.0
```

### Streamlit (.streamlit/secrets.toml)

```toml
[api]
url = "https://your-backend.railway.app/api/v1"
```

---

## Custom Domain Setup (Optional)

### For Backend (Railway)

1. Go to Railway project settings
2. Click "Domains"
3. Add custom domain: `api.yourdomain.com`
4. Add CNAME record in your DNS:
   ```
   CNAME: api.yourdomain.com → your-app.railway.app
   ```

### For Frontend (Streamlit)

1. Streamlit Cloud settings → "Custom domain"
2. Add: `app.yourdomain.com`
3. Add CNAME in DNS:
   ```
   CNAME: app.yourdomain.com → your-app.streamlit.app
   ```

---

## Monitoring & Logs

### Railway Logs

```bash
# View backend logs
railway logs
```

### Streamlit Logs

```bash
# In Streamlit Cloud dashboard
Manage app → Logs
```

### Database Monitoring

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check database size
SELECT pg_size_pretty(pg_database_size('algotrader'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Troubleshooting

### Issue: Backend won't start

**Check:**
1. DATABASE_URL is correct
2. PostgreSQL is running
3. Environment variables are set
4. Requirements.txt is complete

**Fix:**
```bash
# Railway: Check logs
railway logs

# Render: Check logs in dashboard
```

---

### Issue: Frontend can't connect to backend

**Check:**
1. Backend URL is correct in Streamlit secrets
2. CORS_ORIGINS includes Streamlit domain
3. Backend is actually running

**Fix:**
```python
# In streamlit_app.py, add debugging:
st.write(f"API URL: {API_URL}")

try:
    response = requests.get(f"{API_URL}/health")
    st.write(response.json())
except Exception as e:
    st.error(f"Backend error: {str(e)}")
```

---

### Issue: Database connection timeout

**Check:**
1. Database is running
2. Connection string has correct credentials
3. Firewall/network allows connections

**Fix:**
```python
# Add connection pooling
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)
```

---

### Issue: Slow backtests on production

**Optimization:**
```python
# Add database indexes
CREATE INDEX idx_ohlcv_stock_time ON ohlcv_data(stock_id, time DESC);

# Enable query caching
from functools import lru_cache

@lru_cache(maxsize=100)
def get_stock_data(symbol, start_date, end_date):
    # ... fetch from DB
```

---

## Scaling Considerations

### When to upgrade:

**Free Tier Limits:**
- Railway: 500 hours/month = ~16 hours/day
- Streamlit: Unlimited public apps
- Supabase: 500MB storage

**Upgrade if:**
- More than 100 users/day
- Database > 500MB
- Need 24/7 uptime
- Want custom domain SSL

**Cost after free tier:**
- Railway: $5/month (hobby plan)
- Supabase: $25/month (pro plan)
- Total: ~$30/month

---

## Production Best Practices

### ✅ Security

1. **Never commit secrets**:
   ```bash
   # Add to .gitignore
   .env
   *.pem
   *.key
   ```

2. **Use environment variables**:
   ```python
   import os
   DATABASE_URL = os.getenv("DATABASE_URL")
   ```

3. **HTTPS only** (Railway provides free SSL)

### ✅ Performance

1. **Database connection pooling**
2. **Cache frequent queries** (Redis or @lru_cache)
3. **Use CDN for static assets**
4. **Compress responses** (gzip)

### ✅ Reliability

1. **Health checks**:
   ```python
   @app.get("/health")
   async def health():
       # Check DB connection
       db.execute("SELECT 1")
       return {"status": "healthy"}
   ```

2. **Error handling**:
   ```python
   @app.exception_handler(Exception)
   async def handle_exception(request, exc):
       return JSONResponse(
           status_code=500,
           content={"detail": str(exc)}
       )
   ```

3. **Logging**:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.error(f"Backtest failed: {error}")
   ```

---

## Update/Rollback

### Deploy new version:

```bash
# Push to GitHub
git add .
git commit -m "Add new feature"
git push origin main

# Railway auto-deploys
# Streamlit auto-deploys
```

### Rollback:

```bash
# Railway CLI
railway rollback

# OR in Railway dashboard: 
# Deployments → Select previous version → Rollback
```

---

## Cost Breakdown (Monthly)

### Free Tier:
- Backend: FREE (Railway)
- Database: FREE (Railway PostgreSQL)
- Frontend: FREE (Streamlit Cloud)
- **Total: $0/month** ✅

### Paid Tier (for scale):
- Backend: $5 (Railway Hobby)
- Database: $25 (Supabase Pro)
- Frontend: $0 (Streamlit still free)
- Custom Domain: $12/year
- **Total: ~$30/month**

---

## Support

### If deployment fails:

1. **Check Railway docs**: [docs.railway.app](https://docs.railway.app)
2. **Check Streamlit docs**: [docs.streamlit.io](https://docs.streamlit.io)
3. **GitHub Issues**: Open an issue in your repo
4. **Email me**: your.email@example.com

---

**Congratulations! Your AlgoTradeX platform is now live! 🎉**

**Share your deployed link:**
- Frontend: `https://your-app.streamlit.app`
- Backend API: `https://your-backend.railway.app/docs`
- Add these to your resume and LinkedIn!
