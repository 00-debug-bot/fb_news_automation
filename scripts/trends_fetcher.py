"""
Trends Fetcher Module
Fetches top trending USA Google Trends topics using PyTrends
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError
import time
import random

logger = logging.getLogger(__name__)


class TrendsFetcher:
    """Fetch trending topics from Google Trends for USA region"""
    
    def __init__(self):
        """Initialize PyTrends client"""
        self.pytrends = None
        self._init_client()
    
    def _init_client(self):
        """Initialize or reinitialize the PyTrends client"""
        try:
            self.pytrends = TrendReq(hl='en-US', tz=360)  # US timezone
            logger.info("PyTrends client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyTrends client: {e}")
            raise
    
    def fetch_trending_topics(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetch top trending topics from Google Trends for USA
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of dictionaries containing trend information
        """
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            # Get trending searches
            self.pytrends.trending_searches(pn='united_states')
            
            # Get the trending data
            trending_df = self.pytrends.trending_searches(pn='united_states')
            
            if trending_df.empty:
                logger.warning("No trending topics found")
                return []
            
            trends = []
            for _, row in trending_df.head(limit).iterrows():
                trend_data = {
                    'title': str(row[0]).strip(),
                    'traffic': str(row[1]) if len(row) > 1 else 'N/A',
                    'fetched_at': datetime.utcnow().isoformat(),
                    'source': 'google_trends',
                    'region': 'US'
                }
                trends.append(trend_data)
                logger.info(f"Fetched trend: {trend_data['title']}")
            
            logger.info(f"Successfully fetched {len(trends)} trending topics")
            return trends
            
        except ResponseError as e:
            logger.error(f"PyTrends rate limit or response error: {e}")
            # Wait and retry once
            time.sleep(5)
            try:
                self._init_client()
                return self.fetch_trending_topics(limit)
            except Exception as retry_error:
                logger.error(f"Retry failed: {retry_error}")
                return []
        except Exception as e:
            logger.error(f"Error fetching trending topics: {e}")
            return []
    
    def filter_news_related(self, trends: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filter trends to only include news-related topics
        
        Args:
            trends: List of trend dictionaries
            
        Returns:
            Filtered list of news-related trends
        """
        # Keywords that indicate news-related content
        news_keywords = [
            'breaking', 'news', 'update', 'report', 'developing',
            'live', 'just in', 'exclusive', 'investigation', 'scandal',
            'election', 'politics', 'government', 'congress', 'senate',
            'supreme court', 'president', 'white house', 'policy',
            'economy', 'market', 'stock', 'inflation', 'jobs',
            'weather', 'hurricane', 'storm', 'disaster', 'emergency',
            'health', 'vaccine', 'pandemic', 'disease', 'medical',
            'crime', 'trial', 'verdict', 'arrest', 'investigation',
            'war', 'military', 'defense', 'conflict', 'peace',
            'protest', 'rally', 'demonstration', 'strike', 'union',
            'tech', 'technology', 'ai', 'artificial intelligence',
            'space', 'nasa', 'launch', 'mission', 'discovery',
            'sports', 'championship', 'finals', 'trade', 'signing',
            'celebrity', 'award', 'oscar', 'grammy', 'emmy',
            'international', 'global', 'world', 'foreign', 'diplomatic'
        ]
        
        filtered = []
        for trend in trends:
            title_lower = trend['title'].lower()
            
            # Check if any news keyword is in the title
            is_news_related = any(keyword in title_lower for keyword in news_keywords)
            
            # Also include if it looks like a proper news topic
            # (contains multiple words, proper nouns, etc.)
            if not is_news_related:
                # Check if it's a multi-word topic that could be news
                words = trend['title'].split()
                if len(words) >= 2:
                    # Check for capitalized words (proper nouns)
                    capitalized = sum(1 for w in words if w[0].isupper())
                    if capitalized >= 1:
                        is_news_related = True
            
            if is_news_related:
                trend['is_news'] = True
                filtered.append(trend)
                logger.debug(f"News-related trend: {trend['title']}")
            else:
                trend['is_news'] = False
                logger.debug(f"Filtered out: {trend['title']}")
        
        logger.info(f"Filtered {len(filtered)} news-related trends from {len(trends)} total")
        return filtered
    
    def get_daily_trending(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get daily trending searches
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of daily trending topics
        """
        try:
            time.sleep(random.uniform(1, 3))
            
            # Get daily trending searches
            daily_trends = self.pytrends.daily_trends(expiry=0, limit=limit)
            
            if daily_trends.empty:
                return []
            
            trends = []
            for _, row in daily_trends.iterrows():
                trend_data = {
                    'title': str(row['title']).strip() if 'title' in row else str(row.iloc[0]).strip(),
                    'traffic': str(row['traffic']) if 'traffic' in row else 'N/A',
                    'description': str(row['description']) if 'description' in row else '',
                    'fetched_at': datetime.utcnow().isoformat(),
                    'source': 'google_trends_daily',
                    'region': 'US'
                }
                trends.append(trend_data)
            
            return self.filter_news_related(trends)
            
        except Exception as e:
            logger.error(f"Error fetching daily trends: {e}")
            return []


def main():
    """Test the trends fetcher"""
    logging.basicConfig(level=logging.INFO)
    fetcher = TrendsFetcher()
    
    print("Fetching trending topics...")
    trends = fetcher.fetch_trending_topics(limit=10)
    
    if trends:
        print(f"\nFound {len(trends)} trending topics:")
        for i, trend in enumerate(trends[:5], 1):
            print(f"{i}. {trend['title']} (Traffic: {trend['traffic']})")
    
    print("\nFiltering news-related topics...")
    news_trends = fetcher.filter_news_related(trends)
    
    if news_trends:
        print(f"\nFound {len(news_trends)} news-related trends:")
        for i, trend in enumerate(news_trends[:5], 1):
            print(f"{i}. {trend['title']}")
    else:
        print("No news-related trends found")


if __name__ == "__main__":
    main()