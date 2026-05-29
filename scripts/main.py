"""
Main Automation Script
Orchestrates the complete workflow: fetch trends → get news → generate headline → create image → post to Facebook
"""

import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from scripts.trends_fetcher import TrendsFetcher
from scripts.news_fetcher import NewsFetcher
from scripts.headline_generator import HeadlineGenerator
from scripts.image_processor import ImageProcessor
from scripts.storage import StorageManager
from scripts.facebook_poster import FacebookPoster

# Configure logging
def setup_logging(log_dir: str = None):
    """Setup logging configuration"""
    if log_dir is None:
        log_dir = os.getenv('LOG_DIR', '/app/logs')
    
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'automation_{datetime.utcnow().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


class NewsAutomationSystem:
    """Main automation system orchestrator"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize the automation system
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize components
        self.trends_fetcher = TrendsFetcher()
        self.news_fetcher = NewsFetcher()
        self.headline_generator = HeadlineGenerator()
        self.image_processor = ImageProcessor()
        self.storage = StorageManager()
        self.facebook_poster = FacebookPoster()
        
        # Configuration
        self.max_trends_to_process = self.config.get('max_trends', 1)
        self.duplicate_check_hours = self.config.get('duplicate_hours', 48)
        
        env_skip = os.getenv('SKIP_FACEBOOK', '').lower()
        if env_skip in ('true', '1', 'yes'):
            self.skip_facebook = True
        else:
            self.skip_facebook = self.config.get('skip_facebook', False)
        
        self.logger.info("News Automation System initialized")
    
    def run_cycle(self) -> Dict[str, Any]:
        """
        Run a complete automation cycle
        
        Returns:
            Results dictionary with statistics
        """
        self.logger.info("=" * 50)
        self.logger.info("Starting automation cycle")
        self.logger.info("=" * 50)
        
        results = {
            'cycle_start': datetime.utcnow().isoformat(),
            'trends_found': 0,
            'trends_processed': 0,
            'posts_created': 0,
            'facebook_posts': 0,
            'errors': [],
            'posts': []
        }
        
        try:
            # Step 1: Fetch trending topics
            trends = self._fetch_trends()
            results['trends_found'] = len(trends)
            
            if not trends:
                self.logger.warning("No trending topics found")
                results['errors'].append("No trending topics found")
                return results
            
            # Step 2: Save trends to history
            self.storage.save_trends_batch(trends)
            
            # Step 3: Process each trend
            for trend in trends[:self.max_trends_to_process]:
                try:
                    post_result = self._process_trend(trend)
                    if post_result:
                        results['posts'].append(post_result)
                        results['trends_processed'] += 1
                        if post_result.get('facebook_post_id'):
                            results['facebook_posts'] += 1
                        results['posts_created'] += 1
                except Exception as e:
                    error_msg = f"Error processing trend '{trend.get('title', 'unknown')}': {str(e)}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Step 4: Cleanup old records periodically
            self.storage.cleanup_old_records(days=30)
            
        except Exception as e:
            error_msg = f"Critical error in automation cycle: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        results['cycle_end'] = datetime.utcnow().isoformat()
        
        self.logger.info("=" * 50)
        self.logger.info(f"Cycle complete. Processed: {results['trends_processed']}, "
                        f"Posted: {results['facebook_posts']}")
        self.logger.info("=" * 50)
        
        return results
    
    def _fetch_trends(self) -> List[Dict]:
        """
        Fetch trending topics from Google Trends
        
        Returns:
            List of filtered news-related trends
        """
        self.logger.info("Fetching trending topics...")
        
        # Fetch trending topics
        trends = self.trends_fetcher.fetch_trending_topics(limit=15)
        
        if not trends:
            # Try daily trends as fallback
            self.logger.info("Trying daily trends as fallback...")
            trends = self.trends_fetcher.get_daily_trending(limit=10)
        
        # Filter to news-related
        news_trends = self.trends_fetcher.filter_news_related(trends)
        
        # Get recently posted topics to avoid duplicates
        recent_topics = self.storage.get_recent_topics(count=20)
        
        # Filter out recently posted topics
        fresh_trends = [
            t for t in news_trends 
            if t['title'] not in recent_topics
        ]
        
        self.logger.info(f"Found {len(fresh_trends)} fresh news trends")
        
        return fresh_trends
    
    def _process_trend(self, trend: Dict) -> Optional[Dict]:
        """
        Process a single trend topic
        
        Args:
            trend: Trend dictionary
            
        Returns:
            Post result dictionary or None
        """
        topic_title = trend.get('title', '')
        
        if not topic_title:
            return None
        
        self.logger.info(f"Processing trend: {topic_title}")
        
        # Check for duplicates
        if self.storage.is_duplicate(topic_title, hours=self.duplicate_check_hours):
            self.logger.info(f"Skipping duplicate topic: {topic_title}")
            return None
        
        # Step 1: Fetch news articles
        article = self.news_fetcher.get_best_article(topic_title)
        
        if not article:
            self.logger.warning(f"No articles found for: {topic_title}")
            return None
        
        self.logger.info(f"Found article: {article.get('title', '')[:50]}...")
        
        # Step 2: Generate headline
        headline = self.headline_generator.generate_headline(
            trend_topic=topic_title,
            article_title=article.get('title', ''),
            article_description=article.get('description', '')
        )
        
        if not headline:
            self.logger.warning(f"Failed to generate headline for: {topic_title}")
            return None
        
        self.logger.info(f"Generated headline: {headline}")
        
        # Validate headline
        validation = self.headline_generator.validate_headline(headline)
        if not validation.get('valid', False):
            self.logger.warning(f"Headline validation issues: {validation.get('issues', [])}")
        
        # Step 3: Create news card image
        image_url = article.get('image_url', '')
        
        if not image_url:
            self.logger.warning(f"No image URL for: {topic_title}")
            return None
        
        image_path = self.image_processor.process_from_url(
            image_url=image_url,
            headline=headline
        )
        
        if not image_path:
            self.logger.warning(f"Failed to create news card for: {topic_title}")
            return None
        
        self.logger.info(f"Created news card: {image_path}")
        
        # Step 4: Post to Facebook
        facebook_post_id = None
        
        if not self.skip_facebook:
            try:
                post_result = self.facebook_poster.create_complete_post(
                    image_path=image_path,
                    headline=headline,
                    trend_topic=topic_title
                )
                
                if post_result.get('success'):
                    facebook_post_id = post_result.get('post_id')
                    self.logger.info(f"Posted to Facebook: {facebook_post_id}")
                else:
                    self.logger.warning(f"Failed to post to Facebook: {post_result}")
            except Exception as e:
                self.logger.error(f"Error posting to Facebook: {e}")
        
        # Step 5: Save to storage
        self.storage.save_post(
            topic_data=trend,
            article_data=article,
            headline=headline,
            image_path=image_path,
            facebook_post_id=facebook_post_id
        )
        
        return {
            'topic': topic_title,
            'headline': headline,
            'article_title': article.get('title', ''),
            'image_path': image_path,
            'facebook_post_id': facebook_post_id,
            'posted_at': datetime.utcnow().isoformat()
        }
    
    def process_single_topic(self, topic: str) -> Optional[Dict]:
        """
        Process a single specific topic (for manual testing or n8n webhook)
        
        Args:
            topic: Topic string to process
            
        Returns:
            Post result dictionary or None
        """
        self.logger.info(f"Processing single topic: {topic}")
        
        trend = {
            'title': topic,
            'traffic': 'N/A',
            'fetched_at': datetime.utcnow().isoformat(),
            'source': 'manual',
            'region': 'US'
        }
        
        return self._process_trend(trend)


def run_automation():
    """Main entry point for running the automation"""
    logger = setup_logging()
    
    # Load configuration
    config = {}
    config_path = os.getenv('CONFIG_PATH', '../config/config.json')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
    
    # Create and run automation system
    system = NewsAutomationSystem(config)
    results = system.run_cycle()
    
    # Output results as JSON (for n8n integration)
    print("\n" + "=" * 50)
    print("AUTOMATION RESULTS:")
    print(json.dumps(results, indent=2))
    
    # Return exit code based on success
    if results['errors']:
        return 1
    return 0


def handle_webhook(data: Dict) -> Dict:
    """
    Handle webhook call from n8n
    
    Args:
        data: Webhook data containing topic or full trend data
        
    Returns:
        Results dictionary
    """
    logger = setup_logging()
    
    system = NewsAutomationSystem()
    
    # Check what type of webhook data we received
    if 'topic' in data:
        # Single topic processing
        result = system.process_single_topic(data['topic'])
        return {'success': result is not None, 'result': result}
    
    elif 'trends' in data:
        # Batch processing
        results = []
        for trend in data['trends']:
            result = system._process_trend(trend)
            if result:
                results.append(result)
        return {'success': len(results) > 0, 'results': results}
    
    else:
        # Full cycle
        return system.run_cycle()


if __name__ == "__main__":
    exit_code = run_automation()
    sys.exit(exit_code)