# FB News Automation - AI-Powered Facebook News Card System

A fully automated system that fetches trending news topics, generates engaging headlines using AI, creates professional news card images, and posts them to Facebook automatically.

## 🚀 Features

- **Automated Trending Topics**: Fetches top trending USA Google Trends topics every 30 minutes
- **Smart News Filtering**: Filters trends to news-related topics only
- **Article Fetching**: Uses NewsAPI to get latest articles with images
- **AI Headline Generation**: Uses OpenRouter free models to create engaging headlines
- **Professional News Cards**: Creates 1080x1080 images with:
  - Dark gradient overlay
  - Red "BREAKING" label
  - Bold white headline
  - Watermark/logo
  - Contrast enhancement
- **Automatic Facebook Posting**: Posts to Facebook Page using Graph API
- **Duplicate Prevention**: SQLite/JSON storage to avoid posting same topics
- **Error Handling & Logging**: Comprehensive logging and retry mechanisms

## 📁 Project Structure

```
fb_news_automation/
├── scripts/
│   ├── __init__.py
│   ├── trends_fetcher.py      # Google Trends fetching
│   ├── news_fetcher.py        # NewsAPI integration
│   ├── headline_generator.py  # OpenRouter AI headlines
│   ├── image_processor.py     # Pillow image processing
│   ├── facebook_poster.py     # Facebook Graph API
│   ├── storage.py             # SQLite/JSON storage
│   └── main.py                # Main automation orchestrator
├── config/
│   └── config.json            # Configuration file
├── n8n_workflow/
│   └── fb_news_automation_workflow.json  # n8n workflow
├── storage/                   # SQLite database (created at runtime)
├── output/                    # Generated news cards (created at runtime)
├── logs/                      # Log files (created at runtime)
├── .env.example               # Environment variables template
├── .gitignore
├── .dockerignore
├── Dockerfile                 # Docker image for Railway
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🛠️ Prerequisites

### Required API Keys (All Free)

1. **NewsAPI** - Get free key from [newsapi.org](https://newsapi.org/register)
2. **OpenRouter** - Get free key from [openrouter.ai](https://openrouter.ai/keys)
3. **Facebook Page Access Token** - From Facebook Developer Dashboard

### System Requirements

- Python 3.9+
- Docker (for Railway deployment)
- n8n (for workflow automation)

## 📦 Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fb_news_automation
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the automation**
   ```bash
   python scripts/main.py
   ```

### Railway Deployment

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Initialize Railway project**
   ```bash
   railway init
   ```

4. **Set environment variables**
   ```bash
   railway variables set \
     NEWSAPI_KEY=your_key \
     OPENROUTER_API_KEY=your_key \
     FB_PAGE_ACCESS_TOKEN=your_token \
     FB_PAGE_ID=your_page_id
   ```

5. **Deploy**
   ```bash
   railway up
   ```

## ⚙️ Configuration

### Environment Variables (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `NEWSAPI_KEY` | NewsAPI key | Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key | Yes |
| `FB_PAGE_ACCESS_TOKEN` | Facebook Page Access Token | Yes |
| `FB_PAGE_ID` | Facebook Page ID | Yes |
| `MAX_TRENDS` | Max trends to process per cycle | No (default: 3) |
| `DUPLICATE_HOURS` | Hours to check for duplicates | No (default: 48) |
| `SKIP_FACEBOOK` | Skip Facebook posting (for testing) | No (default: false) |
| `STORAGE_DIR` | Directory for storage files | No |
| `OUTPUT_DIR` | Directory for output images | No |
| `LOG_DIR` | Directory for log files | No |

### Configuration File (config/config.json)

The config file allows fine-tuning of:
- Automation parameters
- Trend filtering keywords
- News search settings
- Headline generation options
- Image processing settings
- Facebook API settings

## 🔄 Usage

### Manual Execution

```bash
# Run a single automation cycle
python scripts/main.py

# Run with custom config
CONFIG_PATH=./config/custom.json python scripts/main.py
```

### Scheduled Execution (Cron)

Add to crontab for every 30 minutes:
```bash
*/30 * * * * cd /path/to/fb_news_automation && python scripts/main.py >> logs/cron.log 2>&1
```

### Using n8n Workflow

1. Import `n8n_workflow/fb_news_automation_workflow.json` into n8n
2. Configure environment variables in n8n
3. Activate the workflow
4. The workflow will trigger every 30 minutes automatically

## 🎨 News Card Design

The system creates professional news cards with:

- **Dimensions**: 1080x1080 pixels (Instagram/Facebook optimized)
- **Gradient Overlay**: Dark transparent gradient at bottom
- **BREAKING Label**: Red label in top-left corner
- **Headline**: Bold white text, max 14 words
- **Watermark**: Small logo/text in bottom-right
- **Enhancement**: Slight contrast boost and sharpening

## 📊 Monitoring

### Logs

Logs are stored in `logs/` directory with daily rotation:
- `automation_YYYYMMDD.log`

### Storage

Posted topics are stored in:
- SQLite database: `storage/posted_topics.db`
- Or JSON file: `storage/posted_topics.json`

### Statistics

View posting statistics:
```python
from scripts.storage import StorageManager

storage = StorageManager()
stats = storage.get_post_stats(days=7)
print(stats)
```

## 🛡️ Error Handling

The system includes:
- Automatic retries for API failures
- Fallback headline generation (non-AI)
- Graceful degradation when APIs are unavailable
- Comprehensive error logging
- Duplicate detection to prevent reposting

## 🔧 Troubleshooting

### Common Issues

1. **"No trending topics found"**
   - PyTrends may be rate-limited. Wait a few minutes and retry.
   - Check internet connection.

2. **"No articles found for topic"**
   - The topic may not have recent news coverage.
   - Try a different topic or expand the time range.

3. **"Failed to download image"**
   - Image URL may be blocked or expired.
   - Check firewall/proxy settings.

4. **"Facebook post failed"**
   - Verify Page Access Token is valid.
   - Check token permissions (needs `pages_manage_posts`).
   - Ensure Page ID is correct.

### Getting Help

1. Check logs in `logs/` directory
2. Run with verbose logging: `LOG_LEVEL=DEBUG python scripts/main.py`
3. Test individual components:
   ```bash
   python scripts/trends_fetcher.py
   python scripts/news_fetcher.py
   python scripts/headline_generator.py
   ```

## 📝 License

MIT License - Feel free to use and modify for your projects.

## 🙏 Credits

- **PyTrends** - Google Trends API
- **NewsAPI** - News article search
- **OpenRouter** - AI model access
- **Pillow** - Image processing
- **n8n** - Workflow automation
- **Railway** - Cloud deployment

## 🔄 Updates

### v1.0.0 (Initial Release)
- Complete automation system
- Google Trends integration
- NewsAPI integration
- OpenRouter AI headlines
- Professional image generation
- Facebook auto-posting
- Railway deployment support
- n8n workflow included

---

**Note**: This system is designed for educational purposes. Ensure you comply with all API terms of service and Facebook's platform policies when using this automation.