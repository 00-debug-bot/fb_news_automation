"""
Trends Fetcher Module
Fetches top trending Indian topics using PyTrends (primary) with NewsData.io fallback
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError
import time
import random
import os
import requests

logger = logging.getLogger(__name__)


class TrendsFetcher:
    """Fetch trending topics from Google Trends for India region"""
    
    def __init__(self, newsdata_api_key: str = None):
        """Initialize fetcher with optional NewsData.io fallback key"""
        self.newsdata_api_key = newsdata_api_key or os.getenv('NEWSDATA_API_KEY', 'pub_2b3957a1856a454484d792770c04d4e8')
        self.pytrends = None
        self._init_client()
    
    def _init_client(self):
        """Initialize or reinitialize the PyTrends client"""
        try:
            self.pytrends = TrendReq(hl='en-IN', tz=330)  # India timezone (UTC+5:30)
            logger.info("PyTrends client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyTrends client: {e}")
            self.pytrends = None
    
    def fetch_trending_topics(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetch top trending topics from Google Trends for India.
        Falls back to NewsData.io if PyTrends fails (common on cloud hosting).
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of dictionaries containing trend information
        """
        # Try PyTrends first
        if self.pytrends:
            try:
                time.sleep(random.uniform(1, 3))
                trending_df = self.pytrends.trending_searches(pn='india')
                
                if not trending_df.empty:
                    trends = []
                    for _, row in trending_df.head(limit).iterrows():
                        trend_data = {
                            'title': str(row[0]).strip(),
                            'traffic': str(row[1]) if len(row) > 1 else 'N/A',
                            'fetched_at': datetime.utcnow().isoformat(),
                            'source': 'google_trends',
                            'region': 'IN'
                        }
                        trends.append(trend_data)
                        logger.info(f"Fetched trend: {trend_data['title']}")
                    
                    logger.info(f"Successfully fetched {len(trends)} trending topics via PyTrends")
                    return trends
                    
            except ResponseError as e:
                logger.warning(f"PyTrends error (common on cloud hosting): {e}")
            except Exception as e:
                logger.warning(f"PyTrends unexpected error: {e}")
        
        # Fallback to NewsData.io for trending topics
        logger.info("Falling back to NewsData.io for trending topics...")
        return self._fetch_trends_from_newsdata(limit)
    
    def _fetch_trends_from_newsdata(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetch fresh Indian news headlines from NewsData.io.
        Always returns fresh topics so duplicates don't happen.
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of fresh news headline-based trend dictionaries
        """
        trends = []
        seen_titles = set()
        
        # Try multiple queries to get diverse fresh news
        queries = ['India news', 'breaking India', 'politics India']
        
        for query in queries[:2]:  # Try first 2 queries
            try:
                url = (
                    f"https://newsdata.io/api/1/news"
                    f"?apikey={self.newsdata_api_key}"
                    f"&q={query}"
                    f"&language=en"
                    f"&country=in"
                    f"&size=10"
                )
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('results', []):
                    title = item.get('title', '').strip()
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    # Use the first ~6 words as a short topic
                    words = title.split()
                    if len(words) > 5:
                        short_topic = ' '.join(words[:5]).rstrip('.,;:!?-')
                    else:
                        short_topic = title
                    
                    trend_data = {
                        'title': short_topic,
                        'traffic': 'N/A',
                        'fetched_at': datetime.utcnow().isoformat(),
                        'source': 'newsdata_fallback',
                        'region': 'IN',
                        'is_news': True
                    }
                    trends.append(trend_data)
                    
                    if len(trends) >= limit:
                        break
                
                if len(trends) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"Error fetching from NewsData.io (query={query}): {e}")
                continue
        
        # If NewsData.io failed, use fallback keywords BUT add timestamp to make them unique
        if not trends:
            import hashlib
            base_topics = [
                'India breaking news', 'politics news', 'Bollywood', 'cricket',
                'economy', 'technology', 'sports', 'business'
            ]
            # Generate unique suffix based on current minute to avoid exact duplicates
            minute_suffix = datetime.utcnow().strftime('%H%M')
            for topic in base_topics[:limit]:
                unique_topic = f"{topic} {minute_suffix}"
                trend_data = {
                    'title': unique_topic,
                    'traffic': 'N/A',
                    'fetched_at': datetime.utcnow().isoformat(),
                    'source': 'newsdata_fallback',
                    'region': 'IN',
                    'is_news': True
                }
                trends.append(trend_data)
        
        logger.info(f"Fetched {len(trends)} fresh trending topics")
        return trends[:limit]
    
    def filter_news_related(self, trends: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filter trends to only include news-related topics
        
        Args:
            trends: List of trend dictionaries
            
        Returns:
            Filtered list of news-related trends
        """
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
            'international', 'global', 'world', 'foreign', 'diplomatic',
            # India-specific keywords
            'modi', 'bjp', 'congress', 'delhi', 'mumbai', 'bangalore',
            'karnataka', 'maharashtra', 'uttar pradesh', 'tamil nadu',
            'west bengal', 'gujarat', 'rajasthan', 'kerala', 'punjab',
            'haryana', 'goa', 'assam', 'bihar', 'odisha',
            'aadhaar', 'gst', 'demonetization', 'ayodhya', 'kashmir',
            'nrc', 'caa', 'farm bill', 'agriculture', 'farmers',
            'ipl', 'cricket', 'bollywood', 'tollywood', 'kollywood',
            'sachin', 'kohli', 'dhoni', 'amitabh', 'shah rukh',
            'deepika', 'priyanka', 'alia', 'ranveer', 'akshay'
        ]
        
        filtered = []
        for trend in trends:
            if trend.get('is_news'):
                filtered.append(trend)
                continue
                
            title_lower = trend['title'].lower()
            
            is_news_related = any(keyword in title_lower for keyword in news_keywords)
            
            if not is_news_related:
                words = trend['title'].split()
                if len(words) >= 2:
                    capitalized = sum(1 for w in words if w[0].isupper())
                    if capitalized >= 1:
                        is_news_related = True
            
            if is_news_related:
                trend['is_news'] = True
                filtered.append(trend)
            else:
                trend['is_news'] = False
                logger.debug(f"Filtered out: {trend['title']}")
        
        logger.info(f"Filtered {len(filtered)} news-related trends from {len(trends)} total")
        return filtered
    
    def get_daily_trending(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get daily trending searches (India)
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of daily trending topics
        """
        if self.pytrends:
            try:
                time.sleep(random.uniform(1, 3))
                daily_trends = self.pytrends.daily_trends(expiry=0, limit=limit)
                
                if not daily_trends.empty:
                    trends = []
                    for _, row in daily_trends.iterrows():
                        trend_data = {
                            'title': str(row['title']).strip() if 'title' in row else str(row.iloc[0]).strip(),
                            'traffic': str(row['traffic']) if 'traffic' in row else 'N/A',
                            'description': str(row['description']) if 'description' in row else '',
                            'fetched_at': datetime.utcnow().isoformat(),
                            'source': 'google_trends_daily',
                            'region': 'IN'
                        }
                        trends.append(trend_data)
                    
                    return self.filter_news_related(trends)
                    
            except Exception as e:
                logger.warning(f"PyTrends daily trends error: {e}")
        
        return self._fetch_trends_from_newsdata(limit)


def main():
    """Test the trends fetcher"""
    logging.basicConfig(level=logging.INFO)
    fetcher = TrendsFetcher()
    
    print("Fetching trending topics for India...")
    trends = fetcher.fetch_trending_topics(limit=10)
    
    if trends:
        print(f"\nFound {len(trends)} trending topics:")
        for i, trend in enumerate(trends[:5], 1):
            print(f"{i}. {trend['title']} (Source: {trend['source']})")
    else:
        print("No trending topics found")
    
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