# 🚀 Setup & Testing Guide

## Quick Start

### 1. Install Dependencies
```bash
cd "/Volumes/University Material/Semester Projects/Ai Project copy"
pip install -r requirements.txt
```

### 2. Reset Database & Create Admin (Optional)
```bash
python reset_database.py
```
**Type `DELETE ALL` when prompted to confirm**

### 3. Start the Application
```bash
python app.py
```

You'll see:
```
✅ Admin user created: syedaliturab@gmail.com
🚀 Digital Lab AI Calling Agent
📱 Starting server...
🌐 Open your browser to: http://localhost:5001
👤 Admin login: syedaliturab@gmail.com / Admin@123
```

---

## Admin Access

**Admin Credentials:**
- Email: `syedaliturab@gmail.com`
- Password: `Admin@123`

**Admin Dashboard:** http://localhost:5001/admin

---

## Email Configuration (Optional)

To enable email verification, update `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Generate this in Gmail settings
```

**Without SMTP:** Verification codes will print to console during development.

---

##Testing Checklist

### ✅ Multi-User Test
1. Open browser in normal mode → Sign up user 1 → Start call
2. Open incognito browser → Sign up user 2 → Start call
3. Verify both calls work simultaneously ✅

### ✅ Rate Limiting Test
1. Try signing up 11 times in an hour
2. Should get rate limit error after 10 attempts

### ✅ Security Tests
- Try deleting another user's conversation → Should fail ✅
- Try deleting another user's agent → Should fail ✅

### ✅ Email Verification (with SMTP configured)
1. Sign up with real email
2. Check inbox for 6-digit code
3. Enter code to verify

---

## What Changed

### Backend (`app.py`)
- ✅ Removed global `current_call` variable
- ✅ All endpoints now use database-based state
- ✅ Added rate limiting (doubled values)
- ✅ Standardized error responses
- ✅ Added ownership checks
- ✅ Removed unused SocketIO

### Database (`database.py`)
- ✅ Added `update_conversation_metadata()`
- ✅ Added `get_conversation_metadata()`
- ✅ Added `clear_all_data()`

### Auth (`auth.py`)
- ✅ Added `send_verification_email()`
- ✅ Added `verify_email_code()`
- ✅ Added `send_password_reset_email()`
- ✅ Added `reset_password_with_code()`
- ✅ Added `delete_agent()`
- ✅ Added `create_admin_user()`

### Frontend (`main.js`)
- ✅ Updated `sendMessage()` to pass `conversation_id`
- ✅ Updated `endCall()` to pass `conversation_id`

---

## File Changes Summary

| File | Status | Changes |
|------|--------|---------|
| `app.py` | ✅ Updated | Multi-user support, rate limiting, logging |
| `database.py` | ✅ Updated | Helper methods for metadata |
| `auth.py` | ✅ Updated | Email verification, password reset |
| `main.js` | ✅ Updated | conversation_id support |
| `requirements.txt` | ✅ Updated | Added bcrypt, PyJWT, Flask-Limiter |
| `.env` | ✅ Updated | JWT_SECRET, SMTP config |
| `reset_database.py` | ✅ Created | Database reset script |

---

## Troubleshooting

### Issue: Rate limit errors immediately
**Fix:** Rate limits are per-IP. Restart the server to reset limits.

### Issue: Email not sending
**Fix:** Check SMTP credentials in `.env`. In development codes print to console.

### Issue: Admin can't log in
**Fix:** Run `python reset_database.py` to recreate admin user.

---

## Next Steps

1. ✅ Test all functionality
2. ✅ Configure SMTP for production
3. ✅ Deploy to production server
4. ✅ Update `.env` with production secrets
5. ✅ Set up SSL/HTTPS

---

**Everything is ready to go! 🎉**
