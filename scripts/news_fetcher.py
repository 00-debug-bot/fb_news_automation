"""
News Fetcher Module
Fetches latest news articles using NewsAPI
"""

import logging
from typing import List, Dict, Optional
import os
import requests
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetch news articles from NewsAPI"""
    
    def __init__(self, api_key: str = None, newsdata_api_key: str = None):
        """
        Initialize NewsAPI client
        
        Args:
            api_key: NewsAPI key (or set NEWSAPI_KEY environment variable)
            newsdata_api_key: NewsData.io API key
        """
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')
        self.newsdata_api_key = newsdata_api_key or os.getenv('NEWSDATA_API_KEY', 'pub_2b3957a1856a454484d792770c04d4e8')
        
        if not self.api_key:
            logger.warning("NewsAPI key not provided. Some features may be limited.")
            self.client = None
        else:
            self.client = NewsApiClient(api_key=self.api_key)
            logger.info("NewsAPI client initialized")
    
    def search_articles(self, query: str, language: str = 'en', 
                       country: str = 'us', page_size: int = 5,
                       sort_by: str = 'relevancy') -> List[Dict[str, str]]:
        """
        Search for articles related to a query
        """
        articles = []
        if self.client:
            try:
                from_date = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%S')
                to_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
                
                logger.info(f"Searching articles for: '{query}' via NewsAPI")
                
                all_articles = self.client.get_everything(
                    q=query,
                    from_param=from_date,
                    to=to_date,
                    language=language,
                    sort_by=sort_by,
                    page_size=page_size
                )
                
                for article in all_articles['articles']:
                    if article['title'] == '[Removed]':
                        continue
                    
                    article_data = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'image_url': article.get('urlToImage', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'author': article.get('author', ''),
                        'query': query,
                        'fetched_at': datetime.utcnow().isoformat()
                    }
                    
                    if article_data['title']:
                        articles.append(article_data)
                
                if articles:
                    logger.info(f"Found {len(articles)} articles for '{query}' via NewsAPI")
                    return articles
                
            except NewsAPIException as e:
                logger.error(f"NewsAPI error: {e}")
            except Exception as e:
                logger.error(f"Error fetching articles from NewsAPI: {e}")

        # Fallback to NewsData.io
        logger.info(f"Falling back to NewsData.io for query: '{query}'")
        return self._fetch_from_newsdata(query, language, country, page_size)
    
    def _fetch_from_newsdata(self, query: str, language: str = 'en', country: str = 'us', page_size: int = 5) -> List[Dict[str, str]]:
        if not self.newsdata_api_key:
            logger.error("NewsData.io API key not available for fallback.")
            return []
            
        try:
            url = f"https://newsdata.io/api/1/news?apikey={self.newsdata_api_key}&q={quote_plus(query)}&language={language}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for item in data.get('results', [])[:page_size]:
                article_data = {
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'url': item.get('link', ''),
                    'image_url': item.get('image_url', ''),
                    'published_at': item.get('pubDate', ''),
                    'source': item.get('source_id', ''),
                    'author': item.get('creator', [''])[0] if item.get('creator') else '',
                    'query': query,
                    'fetched_at': datetime.utcnow().isoformat()
                }
                if article_data['title']:
                    articles.append(article_data)
                    
            logger.info(f"Found {len(articles)} articles for '{query}' via NewsData.io")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from NewsData.io: {e}")
            return []
    
    def get_top_headlines(self, query: str, country: str = 'us', 
                         page_size: int = 5) -> List[Dict[str, str]]:
        """
        Get top headlines for a query
        """
        articles = []
        if self.client:
            try:
                logger.info(f"Fetching top headlines for: '{query}' via NewsAPI")
                
                headlines = self.client.get_top_headlines(
                    q=query,
                    country=country,
                    page_size=page_size
                )
                
                for article in headlines['articles']:
                    if article['title'] == '[Removed]':
                        continue
                    
                    article_data = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'image_url': article.get('urlToImage', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'query': query,
                        'fetched_at': datetime.utcnow().isoformat()
                    }
                    
                    if article_data['title']:
                        articles.append(article_data)
                
                if articles:
                    return articles
                
            except NewsAPIException as e:
                logger.error(f"NewsAPI error: {e}")
            except Exception as e:
                logger.error(f"Error fetching headlines from NewsAPI: {e}")

        # Fallback to NewsData.io
        logger.info(f"Falling back to NewsData.io for headlines: '{query}'")
        return self._fetch_from_newsdata(query, 'en', country, page_size)
    
    def get_best_article(self, query: str) -> Optional[Dict[str, str]]:
        """
        Get the best article for a query (has image and description)
        
        Args:
            query: Search query
            
        Returns:
            Best article dictionary or None
        """
        # Try search first
        articles = self.search_articles(query, page_size=10)
        
        # Filter for articles with images
        articles_with_images = [a for a in articles if a.get('image_url')]
        
        if articles_with_images:
            return articles_with_images[0]
        
        # Fallback to any article
        if articles:
            return articles[0]
        
        # Try top headlines as fallback
        headlines = self.get_top_headlines(query, page_size=10)
        headlines_with_images = [h for h in headlines if h.get('image_url')]
        
        if headlines_with_images:
            return headlines_with_images[0]
        
        if headlines:
            return headlines[0]
        
        return None
    
    def validate_article(self, article: Dict[str, str]) -> bool:
        """
        Validate that an article has required fields
        
        Args:
            article: Article dictionary
            
        Returns:
            True if valid, False otherwise
        """
        if not article:
            return False
        
        # Must have title
        if not article.get('title'):
            return False
        
        # Check image URL is valid (basic check)
        image_url = article.get('image_url', '')
        if image_url:
            # Should start with http
            if not image_url.startswith(('http://', 'https://')):
                return False
        
        return True


def main():
    """Test the news fetcher"""
    logging.basicConfig(level=logging.INFO)
    
    # Will use NEWSAPI_KEY from environment
    fetcher = NewsFetcher()
    
    if not fetcher.client:
        print("NewsAPI key not set. Please set NEWSAPI_KEY environment variable.")
        return
    
    test_queries = ['breaking news', 'politics', 'technology']
    
    for query in test_queries:
        print(f"\nSearching for: {query}")
        articles = fetcher.search_articles(query, page_size=3)
        
        if articles:
            for i, article in enumerate(articles[:2], 1):
                print(f"\n{i}. {article['title']}")
                if article['description']:
                    print(f"   {article['description'][:100]}...")
                if article['image_url']:
                    print(f"   Image: {article['image_url'][:50]}...")
        else:
            print("No articles found")


if __name__ == "__main__":
    main()