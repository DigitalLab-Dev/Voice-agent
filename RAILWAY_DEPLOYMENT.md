# Railway Deployment Guide

## Prerequisites
- Railway account (sign up at railway.app)
- GitHub repository with your code

## Deployment Steps

### 1. Push Code to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect your Flask app

### 3. Set Environment Variables
In Railway dashboard, go to **Variables** tab and add:

```
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET=your_random_secret_key_here_change_in_production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

**Important**: 
- ✅ `.env` is gitignored (credentials are safe)
- ✅ Use `.env.example` as reference
- ✅ Never commit actual `.env` file
- ✅ PORT is automatically set by Railway (no need to add)

### 4. Database Configuration
Railway will automatically create a SQLite database, but for production you should:
- Consider using PostgreSQL (Railway provides this)
- Or use Railway's persistent volume for SQLite

### 5. Deploy
Railway will automatically deploy when you push to GitHub!

## What Was Changed for Railway

### ✅ `app.py`
- Port now uses `os.getenv('PORT', 5001)` instead of hardcoded 5001
- Production mode detection (disables debug in production)
- Dynamic port binding

### ✅ `Procfile`
```
web: gunicorn app:app
```
This tells Railway to use gunicorn instead of Flask's dev server.

### ✅ `requirements.txt`
- Added `gunicorn>=21.2.0` for production server

### ✅ Security
- SMTP credentials are in `.env` (gitignored)
- `.env.example` provided as template
- JWT_SECRET should be changed in production

## Post-Deployment

### Testing
Your app will be available at: `https://your-app-name.up.railway.app`

### Initial Setup
1. Visit your app URL
2. The admin user will be auto-created:
   - Email: `syedaliturab@gmail.com`
   - Password: `Admin@123`
3. **Change the admin password immediately!**

### Monitoring
- Check Railway logs for errors
- Monitor your Groq API usage
- Set up custom domain (optional)

## Troubleshooting

### Port Errors
Railway sets the PORT automatically. If you see port errors, check that app.py uses:
```python
port = int(os.getenv('PORT', 5001))
```

### Database Errors
If SQLite errors occur:
1. Add persistent volume in Railway
2. Or migrate to PostgreSQL (recommended for production)

### Email Not Working
- Verify SMTP credentials in Railway variables
- Check if Gmail app password is correct
- Enable "Less secure app access" or use App Password

## Local Testing
To test locally with production-like settings:
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app:app
```

## Need Help?
- Railway Docs: https://docs.railway.app
- Check Railway logs for detailed error messages
