# Complete Deployment Guide

This guide walks you through deploying the FB News Automation system to Railway with n8n integration.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] GitHub account
- [ ] Railway account (free tier)
- [ ] n8n account (cloud or self-hosted)
- [ ] Facebook Page (with admin access)
- [ ] NewsAPI key (free)
- [ ] OpenRouter API key (free)

## 🔑 Step 1: Get API Keys

### 1.1 NewsAPI Key

1. Go to [newsapi.org/register](https://newsapi.org/register)
2. Sign up for a free account
3. Copy your API key from the dashboard
4. **Note**: Free tier allows 100 requests/day

### 1.2 OpenRouter API Key

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Sign in with Google/GitHub
3. Create a new API key
4. **Note**: Free models available (Mistral 7B, Gemma 7B, etc.)

### 1.3 Facebook Page Access Token

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app (Business type)
3. Add "Facebook Login" product
4. Go to Tools → Graph API Explorer
5. Select your app
6. Get Token → Get Page Access Token
6. Select your page and grant permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `publish_to_groups` (optional)
7. Copy the generated token

### 1.4 Facebook Page ID

1. Go to your Facebook Page
2. Click "About" in the left menu
3. Scroll down to find "Facebook Page ID"
4. Or use [findmyfbid.in](https://findmyfbid.in/)

## 🚀 Step 2: Deploy to Railway

### 2.1 Prepare Your Repository

1. Create a new GitHub repository
2. Push the `fb_news_automation` folder contents to GitHub

### 2.2 Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect the Dockerfile

### 2.3 Configure Environment Variables

In Railway dashboard, go to Variables and add:

```
NEWSAPI_KEY=your_newsapi_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
FB_PAGE_ACCESS_TOKEN=your_facebook_page_token_here
FB_PAGE_ID=your_facebook_page_id_here
MAX_TRENDS=3
DUPLICATE_HOURS=48
SKIP_FACEBOOK=false
```

### 2.4 Deploy

1. Click "Deploy"
2. Wait for build to complete (~2-3 minutes)
3. Click "Generate Domain" to get a public URL
4. Your service is now live!

## 🔗 Step 3: Set Up n8n Workflow

### 3.1 Import Workflow

1. Open your n8n instance
2. Go to Workflows → Import
3. Upload `n8n_workflow/fb_news_automation_workflow.json`

### 3.2 Configure n8n Variables

In n8n, go to Settings → Environment Variables and add:

```
NEWSAPI_KEY=your_newsapi_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
FB_PAGE_ACCESS_TOKEN=your_facebook_page_token_here
FB_PAGE_ID=your_facebook_page_id_here
```

### 3.3 Update Webhook URL

1. In the n8n workflow, find the "Send Notification" node
2. Update the URL to your Railway app's domain:
   ```
   https://your-app.railway.app/run
   ```

### 3.4 Activate Workflow

1. Click "Activate" in the top right
2. The workflow will now run every 30 minutes

## 🧪 Step 4: Test the System

### 4.1 Test Railway Deployment

```bash
# Check health endpoint
curl https://your-app.railway.app/health

# Expected response:
# {"status":"healthy","timestamp":"...","service":"fb-news-automation"}
```

### 4.2 Trigger Manual Run

```bash
# Run full automation cycle
curl -X POST https://your-app.railway.app/run \
  -H "Content-Type: application/json" \
  -d '{}'

# Process a single topic
curl -X POST https://your-app.railway.app/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "Government Shutdown"}'

# Preview without posting
curl -X POST https://your-app.railway.app/preview \
  -H "Content-Type: application/json" \
  -d '{"topic": "Tech Layoffs"}'
```

### 4.3 Check Status

```bash
curl https://your-app.railway.app/status
```

### 4.4 View Logs

In Railway dashboard:
1. Go to your project
2. Click "Deployments"
3. Click "View Logs"

## 📊 Step 5: Monitor and Maintain

### 5.1 Monitor Posts

Check posted topics via API:
```bash
curl https://your-app.railway.app/topics?limit=10
```

### 5.2 View Statistics

```bash
curl https://your-app.railway.app/status
```

### 5.3 Clean Up Old Data

```bash
curl -X POST https://your-app.railway.app/cleanup \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

## 🔧 Troubleshooting

### Issue: "No trending topics found"

**Cause**: PyTrends rate limiting or network issues

**Solution**:
1. Check Railway logs for errors
2. Wait a few minutes and retry
3. Consider adding a proxy if in restricted region

### Issue: "Facebook post failed"

**Cause**: Invalid token or missing permissions

**Solution**:
1. Verify token has `pages_manage_posts` permission
2. Check token hasn't expired (regenerate if needed)
3. Ensure Page ID is correct

### Issue: "OpenRouter API error"

**Cause**: API key invalid or rate limit

**Solution**:
1. Verify API key in Railway variables
2. Check OpenRouter dashboard for usage
3. Try a different free model

### Issue: Railway build fails

**Cause**: Docker build error

**Solution**:
1. Check Railway build logs
2. Verify all files are in repository
3. Test Docker build locally: `docker build .`

## 💰 Cost Breakdown

### Free Tier Usage

| Service | Cost | Limits |
|---------|------|--------|
| Railway | $0 | $5/month credit (sufficient for this app) |
| NewsAPI | $0 | 100 requests/day |
| OpenRouter | $0 | Free models available |
| Facebook | $0 | No limits for Page posting |
| n8n | $0 | Self-hosted or cloud free tier |

**Total Monthly Cost: $0** 🎉

## 🔄 Alternative Deployment Options

### Option A: VPS Deployment (DigitalOcean, Linode)

```bash
# SSH into your VPS
git clone <your-repo>
cd fb_news_automation

# Install Python and dependencies
sudo apt update
sudo apt install python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
nano .env  # Edit with your API keys

# Run with systemd
sudo nano /etc/systemd/system/fb-news.service
```

Systemd service file:
```ini
[Unit]
Description=FB News Automation
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/fb_news_automation
Environment="PATH=/path/to/fb_news_automation/venv/bin"
ExecStart=/path/to/fb_news_automation/venv/bin/python scripts/web_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Option B: Docker Compose (Local/Self-hosted)

```yaml
# docker-compose.yml
version: '3.8'

services:
  fb-news-automation:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    volumes:
      - ./storage:/app/storage
      - ./output:/app/output
      - ./logs:/app/logs
    restart: unless-stopped
```

### Option C: Heroku Deployment

```bash
# Install Heroku CLI
heroku login
heroku create fb-news-automation

# Set buildpack
heroku buildpacks:set heroku/python

# Set environment variables
heroku config:set NEWSAPI_KEY=xxx
heroku config:set OPENROUTER_API_KEY=xxx
heroku config:set FB_PAGE_ACCESS_TOKEN=xxx
heroku config:set FB_PAGE_ID=xxx

# Deploy
git push heroku main
```

## 📞 Support

If you encounter issues:

1. Check the [README.md](README.md) for general help
2. Review logs in Railway dashboard
3. Test individual API endpoints
4. Verify all API keys are valid

## ✅ Final Checklist

Before going live:

- [ ] All API keys are set in Railway
- [ ] Facebook token has correct permissions
- [ ] n8n workflow is activated
- [ ] Health endpoint returns "healthy"
- [ ] Manual trigger works (`/run` endpoint)
- [ ] Logs show no errors
- [ ] Test post appears on Facebook

---

**Congratulations!** Your automated Facebook news system is now live! 🎉

The system will automatically:
- Check for trending topics every 30 minutes
- Generate engaging headlines
- Create professional news cards
- Post to your Facebook Page

Sit back and watch your engagement grow! 📈