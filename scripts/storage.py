"""
Storage Module
Handles SQLite database and JSON file storage for deduplication
"""

import logging
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class StorageManager:
    """Manage storage of posted topics to avoid duplicates"""
    
    def __init__(self, storage_dir: str = None, use_json: bool = False):
        """
        Initialize storage manager
        
        Args:
            storage_dir: Directory for storage files
            use_json: If True, use JSON file instead of SQLite
        """
        self.storage_dir = storage_dir or os.getenv('STORAGE_DIR', '../storage')
        self.use_json = use_json
        
        os.makedirs(self.storage_dir, exist_ok=True)
        
        if not use_json:
            self.db_path = os.path.join(self.storage_dir, 'posted_topics.db')
            self._init_database()
        else:
            self.json_path = os.path.join(self.storage_dir, 'posted_topics.json')
            self._init_json()
        
        logger.info(f"Storage manager initialized at: {self.storage_dir}")
    
    def _init_database(self):
        """Initialize SQLite database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posted_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_title TEXT NOT NULL,
                    headline TEXT,
                    image_path TEXT,
                    facebook_post_id TEXT,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trend_data TEXT,
                    article_data TEXT,
                    UNIQUE(topic_title)
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_topic_title 
                ON posted_topics(topic_title)
            ''')
            
            # Create table for tracking trends fetch history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trends_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trends_count INTEGER,
                    trends_data TEXT
                )
            ''')
            
            conn.commit()
        
        logger.info("SQLite database initialized")
    
    def _init_json(self):
        """Initialize JSON storage file"""
        if not os.path.exists(self.json_path):
            initial_data = {
                'posted_topics': [],
                'trends_history': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            self._write_json(initial_data)
        
        logger.info("JSON storage initialized")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _read_json(self) -> Dict:
        """Read JSON storage file"""
        try:
            with open(self.json_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'posted_topics': [],
                'trends_history': [],
                'last_updated': datetime.utcnow().isoformat()
            }
    
    def _write_json(self, data: Dict):
        """Write to JSON storage file"""
        data['last_updated'] = datetime.utcnow().isoformat()
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def is_duplicate(self, topic_title: str, hours: int = 48) -> bool:
        """
        Check if a topic was already posted
        
        Args:
            topic_title: Topic title to check
            hours: Time window in hours to check for duplicates
            
        Returns:
            True if duplicate, False otherwise
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        if not self.use_json:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM posted_topics 
                    WHERE topic_title = ? AND posted_at > ?
                ''', (topic_title, cutoff_time.isoformat()))
                
                count = cursor.fetchone()[0]
                return count > 0
        else:
            data = self._read_json()
            for post in data.get('posted_topics', []):
                if post['topic_title'] == topic_title:
                    post_time = datetime.fromisoformat(post['posted_at'])
                    if post_time > cutoff_time:
                        return True
            return False
    
    def get_all_topics(self, limit: int = 100) -> List[Dict]:
        """
        Get all posted topics
        
        Args:
            limit: Maximum number of topics to return
            
        Returns:
            List of topic dictionaries
        """
        if not self.use_json:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM posted_topics 
                    ORDER BY posted_at DESC LIMIT ?
                ''', (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        else:
            data = self._read_json()
            topics = data.get('posted_topics', [])
            return sorted(topics, key=lambda x: x.get('posted_at', ''), reverse=True)[:limit]
    
    def save_post(self, topic_data: Dict, article_data: Dict, 
                 headline: str, image_path: str, 
                 facebook_post_id: str = None) -> int:
        """
        Save a posted topic
        
        Args:
            topic_data: Original trend topic data
            article_data: Article data used
            headline: Generated headline
            image_path: Path to generated image
            facebook_post_id: Facebook post ID if posted
            
        Returns:
            ID of saved record
        """
        topic_title = topic_data.get('title', '')
        
        if not self.use_json:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO posted_topics 
                        (topic_title, headline, image_path, facebook_post_id, 
                         trend_data, article_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        topic_title,
                        headline,
                        image_path,
                        facebook_post_id,
                        json.dumps(topic_data),
                        json.dumps(article_data)
                    ))
                    conn.commit()
                    post_id = cursor.lastrowid
                    logger.info(f"Saved post #{post_id}: {topic_title}")
                    return post_id
                except sqlite3.IntegrityError:
                    logger.warning(f"Topic already exists: {topic_title}")
                    # Update existing record
                    cursor.execute('''
                        UPDATE posted_topics 
                        SET headline = ?, image_path = ?, facebook_post_id = ?,
                            trend_data = ?, article_data = ?, posted_at = ?
                        WHERE topic_title = ?
                    ''', (
                        headline, image_path, facebook_post_id,
                        json.dumps(topic_data), json.dumps(article_data),
                        datetime.utcnow().isoformat(), topic_title
                    ))
                    conn.commit()
                    logger.info(f"Updated existing post: {topic_title}")
                    return -1
        else:
            data = self._read_json()
            
            # Check if exists
            existing = None
            for post in data.get('posted_topics', []):
                if post['topic_title'] == topic_title:
                    existing = post
                    break
            
            post_record = {
                'topic_title': topic_title,
                'headline': headline,
                'image_path': image_path,
                'facebook_post_id': facebook_post_id,
                'posted_at': datetime.utcnow().isoformat(),
                'trend_data': topic_data,
                'article_data': article_data
            }
            
            if existing:
                # Update existing
                existing.update(post_record)
                logger.info(f"Updated existing post: {topic_title}")
            else:
                # Add new
                data['posted_topics'].append(post_record)
                logger.info(f"Saved new post: {topic_title}")
            
            self._write_json(data)
            return len(data['posted_topics'])
    
    def save_trends_batch(self, trends: List[Dict]):
        """
        Save a batch of fetched trends for history
        
        Args:
            trends: List of trend dictionaries
        """
        if not self.use_json:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trends_history (trends_count, trends_data)
                    VALUES (?, ?)
                ''', (len(trends), json.dumps(trends)))
                conn.commit()
        else:
            data = self._read_json()
            data['trends_history'].append({
                'fetched_at': datetime.utcnow().isoformat(),
                'trends_count': len(trends),
                'trends_data': trends
            })
            # Keep only last 100 batches
            data['trends_history'] = data['trends_history'][-100:]
            self._write_json(data)
    
    def get_post_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get posting statistics
        
        Args:
            days: Number of days to calculate stats for
            
        Returns:
            Statistics dictionary
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        if not self.use_json:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Total posts in period
                cursor.execute('''
                    SELECT COUNT(*) FROM posted_topics 
                    WHERE posted_at > ?
                ''', (cutoff_time.isoformat(),))
                total_posts = cursor.fetchone()[0]
                
                # Posts with Facebook ID
                cursor.execute('''
                    SELECT COUNT(*) FROM posted_topics 
                    WHERE facebook_post_id IS NOT NULL 
                    AND facebook_post_id != ''
                    AND posted_at > ?
                ''', (cutoff_time.isoformat(),))
                fb_posts = cursor.fetchone()[0]
                
                return {
                    'total_posts': total_posts,
                    'facebook_posts': fb_posts,
                    'period_days': days
                }
        else:
            data = self._read_json()
            posts = data.get('posted_topics', [])
            
            filtered = [p for p in posts 
                       if datetime.fromisoformat(p.get('posted_at', '2000-01-01')) > cutoff_time]
            
            fb_posts = [p for p in filtered if p.get('facebook_post_id')]
            
            return {
                'total_posts': len(filtered),
                'facebook_posts': len(fb_posts),
                'period_days': days
            }
    
    def cleanup_old_records(self, days: int = 30):
        """
        Remove records older than specified days
        
        Args:
            days: Number of days threshold
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        if not self.use_json:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM posted_topics WHERE posted_at < ?
                ''', (cutoff_time.isoformat(),))
                deleted = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted} old records from database")
        else:
            data = self._read_json()
            original_count = len(data.get('posted_topics', []))
            data['posted_topics'] = [
                p for p in data.get('posted_topics', [])
                if datetime.fromisoformat(p.get('posted_at', '2000-01-01')) > cutoff_time
            ]
            deleted = original_count - len(data['posted_topics'])
            self._write_json(data)
            logger.info(f"Cleaned up {deleted} old records from JSON")
    
    def get_recent_topics(self, count: int = 10) -> List[str]:
        """
        Get list of recently posted topic titles
        
        Args:
            count: Number of topics to return
            
        Returns:
            List of topic titles
        """
        topics = self.get_all_topics(limit=count)
        return [t['topic_title'] for t in topics]


def main():
    """Test the storage manager"""
    logging.basicConfig(level=logging.INFO)
    
    storage = StorageManager(storage_dir="../storage")
    
    # Test saving a post
    test_topic = {'title': 'Test Topic', 'traffic': '100k'}
    test_article = {'title': 'Test Article', 'description': 'Test description'}
    
    post_id = storage.save_post(
        topic_data=test_topic,
        article_data=test_article,
        headline="Test Headline",
        image_path="/path/to/image.jpg",
        facebook_post_id="12345"
    )
    print(f"Saved post ID: {post_id}")
    
    # Check duplicate
    is_dup = storage.is_duplicate('Test Topic')
    print(f"Is duplicate: {is_dup}")
    
    # Get stats
    stats = storage.get_post_stats()
    print(f"Stats: {stats}")
    
    # Get recent topics
    recent = storage.get_recent_topics(5)
    print(f"Recent topics: {recent}")


if __name__ == "__main__":
    main()