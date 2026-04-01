# Task 3 - Quick Start Testing Guide

## 📋 Current Status

✅ **Code Complete**: All authentication system files created and committed  
✅ **Committed to GitHub**: 108 changes, 15,948 insertions (Commit: 0d35d03)  
⏳ **Tests Ready**: 10 comprehensive tests created, waiting to run  
⏳ **Database Ready**: Models defined, waiting for table creation  

---

## 🚀 Quick Start (Copy-Paste Commands)

### Step 1: Install Dependencies (2 minutes)

```bash
cd d:\Entrupy_Assignment\backend
pip install passlib[bcrypt] python-jose[cryptography] bcrypt -q
echo "Dependencies installed!"
```

### Step 2: Start Backend Server (Keep Running)

```bash
cd d:\Entrupy_Assignment\backend
python -m uvicorn app.main:app --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

*Leave this terminal open. Backend is running.*

### Step 3: Start Frontend (New Terminal - Keep Running)

```bash
cd d:\Entrupy_Assignment\frontend
npm start
```

**Expected Output**:
```
Compiled successfully!
Local: http://localhost:3000
```

*Leave this terminal open. Frontend is running.*

### Step 4: Run Test Suite (New Terminal)

```bash
cd d:\Entrupy_Assignment\backend
python test_customer_auth.py
```

**Expected Output**:
```
Testing Customer Authentication System
========================================

1. Health Check ... ✓ PASS
2. User Registration ... ✓ PASS
3. User Login ... ✓ PASS
4. Get User Profile ... ✓ PASS
5. Public API Access ... ✓ PASS
6. API Usage Tracking ... ✓ PASS
7. Token Refresh ... ✓ PASS
8. Usage History ... ✓ PASS
9. Invalid Token Rejection ... ✓ PASS
10. Logout ... ✓ PASS

All 10 tests passed! ✓
```

---

## 🧪 Manual Testing Workflow

### Test 1: User Registration

1. **Open Browser**: http://localhost:3000
2. **Click**: "Sign Up" tab
3. **Fill Form**:
   - Full Name: John Doe
   - Username: john_doe
   - Email: john@example.com
   - Password: TestPass123
   - Confirm Password: TestPass123
4. **Click**: "Create Account"
5. **Expected**: Redirects to dashboard, username shows in navbar

### Test 2: User Login

1. **Navigate**: http://localhost:3000 (or click Logout first)
2. **Click**: "Login" tab
3. **Fill Form**:
   - Username: john_doe
   - Password: TestPass123
4. **Click**: "Sign In"
5. **Expected**: Redirects to dashboard, sees username in navbar

### Test 3: API Usage Tracking

1. **From Dashboard**: Click "API Usage" in navbar
2. **Verify Display**:
   - Daily quota: Shows as "X / 1,000 requests"
   - Monthly quota: Shows as "X / 50,000 requests"
   - Progress bars displayed correctly
3. **Click Tab**: "Request History"
4. **Verify Display**:
   - Table shows recent requests
   - Columns: Endpoint, Method, Status, Response Time, Timestamp
   - Each row shows colored method (GET=blue, POST=green, etc.)

### Test 4: User Profile

1. **From Navbar**: Click "Profile"
2. **Verify Display**:
   - Username, Email shown
   - Full Name: John Doe
   - Account Status: Active (green)
   - Member Since: Today's date
3. **Test Edit**: Click "Edit Profile"
4. **Change**: Full Name → "John Updated"
5. **Click**: "Save Changes"
6. **Verify**: Full Name updated

### Test 5: Rate Limiting (Advanced)

1. **Open Browser Console**: F12
2. **Run Script** (paste in console):
```javascript
// Make 1001 requests to test rate limiting
let count = 0;
const token = localStorage.getItem('token');

for (let i = 0; i < 1001; i++) {
  fetch('http://localhost:8000/api/products?limit=1', {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(r => {
    count++;
    if (r.status === 429) {
      console.log(`Request ${count}: HTTP 429 - Rate Limited!`);
    } else if (count % 100 === 0) {
      console.log(`Request ${count}: HTTP 200 - OK`);
    }
  });
}
```
3. **Expected**: After ~1000 successful requests, requests return HTTP 429

### Test 6: Token Expiration

1. **Open Browser Console**: F12
2. **Get Current Token**:
```javascript
console.log(localStorage.getItem('token'));
```
3. **Wait 24 hours** or modify token to test
4. **Try API Request**: Should get 401 Unauthorized
5. **Solution**: Go to Profile → "Copy Current Token" or re-login

### Test 7: Logout & Re-login

1. **From Navbar**: Click "Logout"
2. **Expected**: Redirected to login page, localStorage cleared
3. **Re-login**: Use same credentials again
4. **Verify**: Successfully logged in again

---

## 🔍 Verification Checklist

### Backend Services
- [ ] Backend server starts without errors
- [ ] Database tables created (check terminal for SQLAlchemy logs)
- [ ] Swagger docs accessible: http://localhost:8000/docs

### Authentication
- [ ] Can register new user
- [ ] Can login with credentials
- [ ] JWT token stored in localStorage
- [ ] Can access protected routes after login
- [ ] Shows 401 error if token invalid/expired
- [ ] Shows 429 error after 1000 requests

### Frontend Components
- [ ] Login/Signup form displays correctly
- [ ] Form validation works (reject invalid email, short password)
- [ ] API Usage dashboard shows usage stats
- [ ] Request history table displays requests
- [ ] User Profile shows account info
- [ ] Can edit profile and save changes
- [ ] Logout clears localStorage and redirects

### Database
- [ ] User table created with proper fields
- [ ] UserUsageLog table created with indexes
- [ ] Can query: `SELECT * FROM user WHERE username='john_doe'`
- [ ] Can query: `SELECT COUNT(*) FROM userusagelog WHERE user_id=1`

### API Endpoints
- [ ] POST /api/auth/register → 200 + token
- [ ] POST /api/auth/login → 200 + token
- [ ] GET /api/auth/me → 200 + user data
- [ ] GET /api/auth/usage → 200 + usage stats
- [ ] GET /api/auth/usage/history → 200 + request logs
- [ ] POST /api/auth/refresh-token → 200 + new token
- [ ] POST /api/auth/logout → 200
- [ ] GET /api/products (no auth) → 200 (public access)

---

## 📊 Sample Test Data

### Test User 1
```
Username: alice_smith
Email: alice@example.com
Password: SecurePass123
Full Name: Alice Smith
```

### Test User 2
```
Username: bob_jones
Email: bob@example.com
Password: AnotherPass456
Full Name: Bob Jones
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'passlib'"

**Solution**:
```bash
pip install passlib[bcrypt] python-jose[cryptography] bcrypt
```

### Issue: "Connection refused" to backend

**Solution**:
1. Ensure backend is running: `python -m uvicorn app.main:app --reload`
2. Check if port 8000 is available
3. Kill any existing processes: `netstat -ano | findstr :8000`

### Issue: Frontend shows "Unable to reach server"

**Solution**:
1. Backend not running - start it first
2. CORS issue - backend should allow localhost:3000 requests
3. Check browser console for specific error

### Issue: "User already exists" during registration

**Solution**:
1. Use different username/email
2. Or clear database: Delete `test.db` and restart backend

### Issue: Login shows "Invalid credentials"

**Solution**:
1. Check username and password are correct
2. Verify user was created in registration
3. Check database: `SELECT * FROM user WHERE username='your_username'`

### Issue: "Token expired" error

**Solution**:
1. Tokens expire after 24 hours
2. Click Profile → "Copy Current Token" to refresh
3. Or logout and login again

---

## 📈 Performance Testing

### Load Test (Optional)

Create file `load_test.py`:
```python
import requests
import time

BASE_URL = "http://localhost:8000"
TOKEN = "-YOUR-TOKEN-HERE-"  # Get from localStorage

headers = {"Authorization": f"Bearer {TOKEN}"}

print("Running load test...")
start = time.time()

for i in range(100):
    r = requests.get(f"{BASE_URL}/api/products?limit=1", headers=headers)
    print(f"Request {i+1}: {r.status_code} ({r.elapsed.total_seconds():.3f}s)")

elapsed = time.time() - start
print(f"\n100 requests in {elapsed:.2f}s = {100/elapsed:.1f} req/s")
```

Run:
```bash
python load_test.py
```

Expected: 10-20 requests/second (depending on system)

---

## ✅ Success Criteria

Your Task 3 implementation is **COMPLETE & WORKING** when:

1. ✓ All 10 tests pass (green checkmarks)
2. ✓ Can register new user in UI
3. ✓ Can login with credentials
4. ✓ API Usage dashboard shows stats
5. ✓ Can view request history
6. ✓ Can edit user profile
7. ✓ Rate limit kicks in after 1000 requests
8. ✓ Can logout and login again
9. ✓ No errors in browser console or terminal

---

## 🎯 Next Steps

### Immediate (This Session)
1. ✅ Install dependencies
2. ✅ Start backend & frontend servers  
3. ✅ Run test suite (all 10 tests should pass)
4. ✅ Manually test all workflows

### Following Session (Optional)
1. Add email verification on registration
2. Implement password reset functionality
3. Add two-factor authentication
4. Create admin dashboard for user management
5. Set up email notifications for rate limit approaching
6. Deploy to production (Heroku, AWS, Azure, etc.)

---

## 📚 Documentation

For detailed information about the authentication system, see:
- **AUTHENTICATION_SYSTEM.md** - Complete system documentation
- **PROGRESS.md** - Project progress report
- **app/auth_routes.py** - Read the code comments
- **test_customer_auth.py** - See test implementation

---

## 🔐 Security Notes

- ✅ Passwords are hashed with bcrypt (never stored in plain text)
- ✅ Tokens expire after 24 hours (JWT expiration)
- ✅ Rate limits prevent abuse (1000/day, 50000/month)
- ✅ All requests logged with IP & user agent
- ✅ CORS configured for frontend origin
- ✅ No sensitive data in localStorage except token

**Important**: In production, use real HTTPS, not HTTP.

---

## 💬 Questions?

Check these resources:
1. **API Docs**: http://localhost:8000/docs (Swagger UI)
2. **Code Comments**: Read app/auth_routes.py for implementation details
3. **Test Cases**: See test_customer_auth.py for example usage
4. **Database**: Query SQLite: `sqlite3 test.db`

---

## 🚀 You're Ready to Go!

**Command Summary**:
```bash
# Terminal 1: Install & run backend
cd backend && pip install passlib[bcrypt] python-jose[cryptography] bcrypt && python -m uvicorn app.main:app --reload

# Terminal 2: Run frontend
cd frontend && npm start

# Terminal 3: Run tests
cd backend && python test_customer_auth.py
```

**Expected Result**: 10 tests pass, frontend accessible at http://localhost:3000

Good luck! 🎉
