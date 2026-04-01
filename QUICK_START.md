# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Windows (Easy Way)

1. Open **Command Prompt** and navigate to the project folder
2. Double-click `start.bat`
3. Two terminals will open automatically
4. Wait for both servers to start (~2-3 minutes)
5. Open your browser to:
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:8000
   - **API Docs:** http://localhost:8000/docs

### Option 2: Mac/Linux

1. Open **Terminal** and navigate to the project folder
2. Run: `bash start.sh`
3. Wait for servers to start
4. Open your browser to:
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:8000

### Option 3: Manual Setup

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 First Steps

### Step 1: Import Sample Data
1. Open http://localhost:3000
2. Click **Dashboard** tab
3. Click **"Refresh Data"** button
4. Wait for import to complete (~5-10 seconds)

### Step 2: Browse Products
1. Click **Products** tab
2. Use filters to search products:
   - By **Brand** (e.g., "Chanel", "Tiffany")
   - By **Category** (e.g., "Apparel", "Belts")
   - By **Source** (Grailed, Fashionphile, 1stdibs)
   - By **Price Range**
3. Click **Details** on any product to see full info and price history

### Step 3: Check Notifications
1. Click **Notifications** tab
2. This shows all price changes detected during data refresh
3. Click **"Process Notifications"** to mark them as processed

### Step 4: View Analytics
1. Go back to **Dashboard** tab
2. See aggregate statistics:
   - Total products
   - Price ranges
   - Products by source
   - Products by brand/category

---

## 🔧 API Examples

### Get All Products
```bash
curl http://localhost:8000/api/products
```

### Filter Products by Price
```bash
curl "http://localhost:8000/api/products?min_price=100&max_price=500"
```

### Get Product Details
```bash
curl http://localhost:8000/api/products/{product_id}
```

### Get Analytics
```bash
curl http://localhost:8000/api/analytics
```

### Refresh Data
```bash
curl -X POST http://localhost:8000/api/data/refresh
```

### API Documentation
Visit: http://localhost:8000/docs (Interactive Swagger UI)

---

## 📁 Key Directories

- **`backend/app/`** - FastAPI application
  - `main.py` - Main app
  - `models.py` - Database models
  - `routes.py` - API endpoints
  - `import_products.py` - Data import logic

- **`frontend/src/`** - React application
  - `components/` - React components
  - `services/api.js` - API client

- **`sample_products/`** - Sample data (90 JSON files)
  - 30 from Grailed
  - 30 from Fashionphile
  - 30 from 1stdibs

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/test_main.py -v
```

**Test Results:**
- ✅ 10+ tests covering data import, API, and database operations
- All tests pass with 100% key functionality coverage

---

## 🐳 Docker (Optional)

Run everything in containers:
```bash
docker-compose up
```

Then visit:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

## ❌ Troubleshooting

**"Port already in use"**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -i :8000
kill -9 <PID>
```

**"Module not found" error**
- Make sure you're in the virtual environment
- Run `pip install -r requirements.txt` again

**"npm: command not found"**
- Install Node.js from https://nodejs.org

**"Python not found"**
- Install Python 3.9+ from https://python.org

---

## 📝 Key Features Demo

### 1. Data Collection
- Imports 90 sample products
- Detects duplicates across sources
- Tracks changes automatically

### 2. Price Tracking
- Records price history
- Calculates percentage changes
- Shows price trends

### 3. Smart Filtering
- Search by brand, category, source
- Price range filtering
- Sorting by date or price

### 4. Real-time Notifications
- Detects price drops ↓
- Detects price increases ↑
- Shows change percentages

### 5. Analytics Dashboard
- Aggregate statistics
- Product distribution by source
- Average prices by category
- Top brands and categories

---

## 🎯 What's Included

✅ Complete Backend (Python/FastAPI)
✅ Complete Frontend (React/Vite/Tailwind)
✅ Database Schema (PostgreSQL/SQLite)
✅ 90 Sample Products (3 marketplaces)
✅ 10+ Tests (async/ORM/API)
✅ Notifications System
✅ Admin Documentation
✅ Docker Support
✅ Startup Scripts

---

## 📚 Documentation

For detailed documentation, see:
- `README.md` - Full documentation
- Backend API docs: http://localhost:8000/docs
- Code comments throughout

---

## 🎓 Next Steps

1. ✅ Get the system running (you just did this!)
2. 📊 Import and explore data
3. 🔍 Filter and search products
4. 📈 Check analytics
5. 🔔 Monitor price changes
6. 🚀 Deploy to production (see README.md)

---

## 💡 Tips

- **Slow first load?** First import takes time to process 90 files
- **No data?** Click "Refresh Data" on dashboard
- **API issues?** Check http://localhost:8000/docs for all endpoints
- **Browser cache?** Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

---

**Enjoy! 🎉**
