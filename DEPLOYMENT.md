# 🚀 Vercel Deployment Guide

Complete guide to deploy your Enhanced Journaling Engine to Vercel with PostgreSQL database.

## 📋 Prerequisites

- [Vercel Account](https://vercel.com)
- [GitHub Account](https://github.com)
- [Vercel CLI](https://vercel.com/docs/cli) (optional)

## 🗄️ Database Setup

### Option 1: Vercel Postgres (Recommended)

1. **Create Vercel Postgres Database**:
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Login to Vercel
   vercel login
   
   # Create Postgres database
   vercel storage create postgres
   ```

2. **Get Database URL**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Navigate to Storage → Your Database
   - Copy the `DATABASE_URL`

### Option 2: External PostgreSQL

You can use any PostgreSQL provider:
- [Supabase](https://supabase.com) (Free tier available)
- [Neon](https://neon.tech) (Free tier available)
- [Railway](https://railway.app)
- [Heroku Postgres](https://heroku.com/postgres)

## 🔧 Database Setup

### 1. Install Prisma CLI
```bash
npm install -g prisma
# or
pip install prisma
```

### 2. Initialize Database
```bash
# Generate Prisma client
prisma generate

# Run database migrations
prisma db push

# (Optional) View database in Prisma Studio
prisma studio
```

### 3. Environment Variables

Create a `.env` file in your project root:
```env
# Database
DATABASE_URL="postgresql://username:password@host:port/database"

# Gemini API (for Enhanced Journaling Engine)
GEMINI_API_KEY="your_gemini_api_key"

# Flask
FLASK_ENV="production"
SECRET_KEY="your-secret-key-here"
```

## 🚀 Deploy to Vercel

### Method 1: Vercel Dashboard (Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add Vercel deployment"
   git push origin main
   ```

2. **Import to Vercel**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Configure settings:
     - **Framework Preset**: Other
     - **Build Command**: `pip install -r requirements.txt`
     - **Output Directory**: `src/web_app`
     - **Install Command**: `pip install -r requirements.txt`

3. **Add Environment Variables**:
   - Go to Project Settings → Environment Variables
   - Add:
     - `DATABASE_URL`
     - `GEMINI_API_KEY`
     - `FLASK_ENV=production`

4. **Deploy**:
   - Click "Deploy"
   - Wait for build to complete

### Method 2: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# Follow prompts to configure:
# - Set up and deploy: Yes
# - Which scope: Your account
# - Link to existing project: No
# - Project name: handwriting-ocr
# - Directory: ./
# - Override settings: No
```

## 🔄 Database Migrations

After deployment, run database migrations:

```bash
# Connect to your Vercel project
vercel link

# Run migrations
vercel env pull .env
prisma db push
```

## 📊 Verify Deployment

1. **Check Health Endpoint**:
   ```
   https://your-app.vercel.app/api/health
   ```

2. **Access Dashboard**:
   ```
   https://your-app.vercel.app/dashboard
   ```

3. **Test Data Collection**:
   ```
   https://your-app.vercel.app/
   ```

## 🛠️ Configuration Files

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "src/web_app/app_enhanced.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "src/web_app/app_enhanced.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production"
  }
}
```

### requirements.txt
Make sure these are included:
```
flask>=2.3.0
prisma>=0.12.0
psycopg2-binary>=2.9.0
gunicorn>=21.0.0
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Error**:
   ```bash
   # Check DATABASE_URL format
   echo $DATABASE_URL
   
   # Test connection
   prisma db pull
   ```

2. **Build Failures**:
   - Check Vercel build logs
   - Ensure all dependencies are in `requirements.txt`
   - Verify Python version compatibility

3. **Import Errors**:
   - Check file paths in imports
   - Ensure all required files are in the repository

### Debug Commands

```bash
# Check Vercel logs
vercel logs

# Check database connection
vercel env pull .env
prisma studio

# Test locally
python src/web_app/app_enhanced.py
```

## 📈 Monitoring

### Vercel Analytics
- Go to your project dashboard
- View Analytics tab for:
  - Page views
  - Performance metrics
  - Error rates

### Database Monitoring
- Vercel Postgres: Built-in monitoring
- External providers: Check their dashboards

## 🔐 Security

### Environment Variables
- Never commit `.env` files
- Use Vercel's environment variable system
- Rotate API keys regularly

### Database Security
- Use connection pooling
- Enable SSL connections
- Regular backups

## 🚀 Production Checklist

- [ ] Database migrations completed
- [ ] Environment variables set
- [ ] Health endpoint responding
- [ ] Dashboard accessible
- [ ] Data collection working
- [ ] Analytics tracking
- [ ] Error monitoring configured
- [ ] SSL certificate active
- [ ] Performance optimized

## 📞 Support

If you encounter issues:

1. Check [Vercel Documentation](https://vercel.com/docs)
2. Review [Prisma Documentation](https://prisma.io/docs)
3. Check build logs in Vercel dashboard
4. Verify environment variables

## 🎉 Success!

Your Enhanced Journaling Engine is now deployed and ready to:
- Collect handwriting data with improved UI/UX
- Track labeled vs unlabeled images
- Store color-coded journal entries
- Provide analytics and project management
- Export data for OCR training

Visit your deployed URL and start creating projects! 🚀
