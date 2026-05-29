# Quick Setup Instructions

Follow these steps to get your FB News Automation system running in under 15 minutes.

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Your API Keys

#### NewsAPI (1 minute)
1. Visit [newsapi.org/register](https://newsapi.org/register)
2. Sign up with email
3. Copy your API key

#### OpenRouter (1 minute)
1. Visit [openrouter.ai/keys](https://openrouter.ai/keys)
2. Sign in with Google
3. Click "Create Key"
4. Copy your API key

#### Facebook (3 minutes)
1. Visit [Facebook Developers](https://developers.facebook.com/)
2. Create a new app (select "Business")
3. Go to Tools → Graph API Explorer
4. Select your app → Get Token → Get Page Access Token
5. Select your page → Copy token
6. Get your Page ID from [findmyfbid.in](https://findmyfbid.in/)

### Step 2: Deploy to Railway

1. **Fork/Clone this repo** to your GitHub

2. **Deploy on Railway**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Add Environment Variables** (in Railway dashboard):
   ```
   NEWSAPI_KEY=paste_your_newsapi_key
   OPENROUTER_API_KEY=paste_your_openrouter_key
   FB_PAGE_ACCESS_TOKEN=paste_your_fb_token
   FB_PAGE_ID=paste_your_page_id
   ```

4. **Deploy** - Railway will automatically build and deploy

5. **Generate Domain** - Click "Generate Domain" to get a public URL

### Step 3: Test Your Deployment

Open your browser and visit:
```
https://your-app.railway.app/health
```

You should see:
```json
{"status":"healthy","timestamp":"...","service":"fb-news-automation"}
```

### Step 4: Test a Manual Post

```bash
curl -X POST https://your-app.railway.app/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "Breaking News"}'
```

Check your Facebook Page - you should see a new post!

## 📋 Detailed Setup (Local Development)

### Prerequisites
- Python 3.9+
- pip (Python package manager)
- Git

### Installation

```bash
# 1. Clone repository
git clone https://github.com/your-username/fb-news-automation.git
cd fb-news-automation

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment file
cp .env.example .env

# 6. Edit .env with your API keys
nano .env  # or use your preferred editor
```

### Run Locally

```bash
# Run the automation
python scripts/main.py

# Or run the web server
python scripts/web_server.py
```

## 🎨 Customization

### Change Number of Posts Per Cycle

Edit `config/config.json`:
```json
{
    "automation": {
        "max_trends": 5  // Change from 3 to 5
    }
}
```

### Change Headline Style

Edit `scripts/headline_generator.py` and modify the prompt in `_get_prompt()` method.

### Add Your Logo

1. Create a 120x120 PNG with transparency
2. Save as `logo.png` in the root directory
3. Edit `config/config.json`:
```json
{
    "image": {
        "watermark_text": "",  // Clear text
        "logo_path": "logo.png"  // Add your logo
    }
}
```

## 🔧 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --upgrade
```

### "API key not valid" errors
- Double-check your API keys in Railway variables
- Ensure no extra spaces in the values

### "No trending topics found"
- Wait 5 minutes and retry (PyTrends rate limiting)
- Check Railway logs for details

### "Facebook post failed"
- Verify your Page Access Token has `pages_manage_posts` permission
- Ensure your Page ID is correct (numbers only)

## 📞 Need Help?

1. Check the [README.md](README.md) for detailed documentation
2. Review the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions
3. Check Railway logs in the dashboard
4. Test individual components:
   ```bash
   python scripts/trends_fetcher.py
   python scripts/news_fetcher.py
   python scripts/headline_generator.py
   ```

## ✅ Verification Checklist

After setup, verify:

- [ ] Health endpoint returns "healthy"
- [ ] `/status` endpoint shows statistics
- [ ] Manual trigger creates a news card
- [ ] Post appears on Facebook Page
- [ ] Logs show no errors

**You're all set!** 🎉

The system will now automatically post trending news to your Facebook Page every 30 minutes.