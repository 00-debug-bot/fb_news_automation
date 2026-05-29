"""
News Fetcher Module
Fetches latest news articles using NewsData.io (primary) with fallback to NewsAPI
"""

import logging
from typing import List, Dict, Optional
import os
import requests
from urllib.parse import quote_plus
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetch news articles — primary source: NewsData.io, fallback: NewsAPI"""
    
    def __init__(self, newsdata_api_key: str = None, newsapi_key: str = None):
        """
        Initialize news fetcher
        
        Args:
            newsdata_api_key: NewsData.io API key (or set NEWSDATA_API_KEY env var)
            newsapi_key: NewsAPI key fallback (or set NEWSAPI_KEY env var)
        """
        self.newsdata_api_key = (newsdata_api_key or os.getenv('NEWSDATA_API_KEY', 'pub_2b3957a1856a454484d792770c04d4e8')).strip()
        self.newsapi_key = newsapi_key or os.getenv('NEWSAPI_KEY')
        
        if not self.newsdata_api_key:
            logger.warning("NewsData.io API key not set. Set NEWSDATA_API_KEY environment variable.")
        else:
            logger.info("NewsData.io client initialized")
    
    def _fetch_from_newsdata(self, query: str, language: str = 'en', country: str = 'in', page_size: int = 5) -> List[Dict[str, str]]:
        """Fetch articles from NewsData.io"""
        if not self.newsdata_api_key:
            logger.warning("NewsData.io API key not set. Cannot fetch.")
            return []
            
        try:
            url = (
                f"https://newsdata.io/api/1/news"
                f"?apikey={self.newsdata_api_key}"
                f"&q={quote_plus(query)}"
                f"&language={language}"
                f"&country={country}"
                f"&size={page_size}"
            )
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for item in data.get('results', [])[:page_size]:
                # Skip removed/invalid entries
                if item.get('title') == '[Removed]' or not item.get('title'):
                    continue
                
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
    
    def _fetch_from_newsapi(self, query: str, language: str = 'en', page_size: int = 5) -> List[Dict[str, str]]:
        """Fallback: Fetch articles from NewsAPI"""
        if not self.newsapi_key:
            logger.warning("NewsAPI key not set. Fallback unavailable.")
            return []
        
        try:
            from_date = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%d')
            url = (
                f"https://newsapi.org/v2/everything"
                f"?q={quote_plus(query)}"
                f"&from={from_date}"
                f"&language={language}"
                f"&sortBy=relevancy"
                f"&pageSize={page_size}"
                f"&apiKey={self.newsapi_key}"
            )
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                if article.get('title') == '[Removed]' or not article.get('title'):
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
            
            logger.info(f"Found {len(articles)} articles for '{query}' via NewsAPI (fallback)")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI fallback: {e}")
            return []
    
    def search_articles(self, query: str, language: str = 'en', 
                       country: str = 'in', page_size: int = 5,
                       sort_by: str = 'relevancy') -> List[Dict[str, str]]:
        """
        Search for articles related to a query
        
        Args:
            query: Search term
            language: Language code (default: 'en')
            country: Country code (default: 'in' for India)
            page_size: Number of results to return
            sort_by: Sort method
        """
        # Primary: NewsData.io
        articles = self._fetch_from_newsdata(query, language, country, page_size)
        if articles:
            return articles
        
        # Fallback: NewsAPI
        logger.info(f"Falling back to NewsAPI for query: '{query}'")
        return self._fetch_from_newsapi(query, language, page_size)
    
    def get_top_headlines(self, query: str, country: str = 'in', 
                         page_size: int = 5) -> List[Dict[str, str]]:
        """
        Get top headlines for a query (India-focused)
        
        Args:
            query: Search term
            country: Country code (default: 'in' for India)
            page_size: Number of results
        """
        # Use NewsData.io search as top headlines equivalent
        articles = self._fetch_from_newsdata(query, 'en', country, page_size)
        if articles:
            return articles
        
        # Fallback to NewsAPI headlines
        if self.newsapi_key:
            try:
                url = (
                    f"https://newsapi.org/v2/top-headlines"
                    f"?q={quote_plus(query)}"
                    f"&country={country}"
                    f"&pageSize={page_size}"
                    f"&apiKey={self.newsapi_key}"
                )
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                articles = []
                for article in data.get('articles', []):
                    if article.get('title') == '[Removed]' or not article.get('title'):
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
            except Exception as e:
                logger.error(f"Error fetching headlines from NewsAPI: {e}")
        
        return []
    
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
            if not image_url.startswith(('http://', 'https://')):
                return False
        
        return True


def main():
    """Test the news fetcher"""
    logging.basicConfig(level=logging.INFO)
    
    fetcher = NewsFetcher()
    
    test_queries = ['breaking news India', 'politics', 'technology', 'Bollywood', 'cricket']
    
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