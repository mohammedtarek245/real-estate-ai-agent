# Deployment Guide for Real Estate AI Agent

## Project Overview
This is an AI-powered real estate recommendation system with a WhatsApp-style interface, specialized in Arabic dialect support and intelligent property matching.

## Files to Include in Your ZIP Upload
When downloading this project for deployment, ensure you include all these files:

1. **Python Files**:
   - `main.py` - Entry point
   - `app.py` - Flask application
   - `models.py` - Database models
   - `Ai_agnet_realestate.py` - AI agent logic

2. **Data Files**:
   - `fake_real_estate_data_with_currency.csv` - Property data

3. **Templates & Static Files**:
   - `templates/` directory (all HTML files)
   - `static/` directory (CSS, JS, images)

## Requirements
When deploying to Render or another platform, ensure your requirements.txt includes:
```
flask>=3.1.1
flask-login>=0.6.3
flask-sqlalchemy>=3.1.1
gunicorn>=23.0.0
pandas>=2.2.3
psycopg2-binary>=2.9.10
sqlalchemy>=2.0.40
werkzeug>=3.1.3
email-validator>=2.2.0
openai>=1.78.1
twilio>=9.6.1
```

## Deployment Steps on Render.com

### Manual Upload Option
1. Go to [Render.com](https://render.com/) and sign up/log in
2. Go to Dashboard → New → Web Service
3. Select "Upload Files" option
4. Upload your ZIP file containing all project files
5. Configure your service:
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --reuse-port --reload main:app`
6. Add environment variables:
   - `SESSION_SECRET` (generate a random string)
   - `DATABASE_URL` (if using PostgreSQL)
7. Click "Create Web Service"

### Database Configuration
For PostgreSQL database:
1. In Render Dashboard, go to "New" → "PostgreSQL"
2. Create a new database
3. Copy the "Internal Connection String"
4. Add it as `DATABASE_URL` environment variable in your web service settings

## Local Testing Before Deployment
Run these commands to test locally:
```
python -m flask run --host=0.0.0.0 --port=5000
```

## Post-Deployment Verification
After deployment, check:
1. Can you load the main page?
2. Does the chat interface appear correctly?
3. Can you send messages and get AI responses?
4. Does the dialect switching work properly?

## Troubleshooting
- If the app won't start, check the logs in Render dashboard
- If database issues occur, verify connection string is correct
- If UI issues occur, check for missing static files