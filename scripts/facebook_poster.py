"""
Facebook Poster Module
Handles posting to Facebook Page using Graph API
"""

import logging
import requests
import os
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class FacebookPoster:
    """Post content to Facebook Page using Graph API"""
    
    def __init__(self, page_access_token: str = None, page_id: str = None):
        """
        Initialize Facebook poster
        
        Args:
            page_access_token: Facebook Page Access Token
            page_id: Facebook Page ID
        """
        self.page_access_token = (page_access_token or os.getenv('FB_PAGE_ACCESS_TOKEN', '')).strip()
        self.page_id = (page_id or os.getenv('FB_PAGE_ID', '')).strip()
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.page_access_token:
            logger.warning("Facebook Page Access Token not configured")
        if not self.page_id:
            logger.warning("Facebook Page ID not configured")
        
        logger.info(f"Facebook Poster initialized for Page ID: {self.page_id}")
    
    def post_photo(self, image_path: str, message: str = "") -> Optional[str]:
        """
        Post a photo to Facebook Page
        
        Args:
            image_path: Path to image file
            message: Caption/message for the post
            
        Returns:
            Post ID if successful, None otherwise
        """
        if not self.page_access_token or not self.page_id:
            logger.error("Facebook credentials not configured")
            return None
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            logger.info(f"Posting photo to Facebook: {image_path}")
            
            url = f"{self.base_url}/{self.page_id}/photos"
            
            with open(image_path, 'rb') as image_file:
                files = {'source': image_file}
                data = {
                    'message': message,
                    'access_token': self.page_access_token
                }
                response = requests.post(url, files=files, data=data, timeout=60)
            
            if not response.ok:
                logger.error(f"Facebook API error {response.status_code}: {response.text}")
                return None
            result = response.json()
            
            if 'id' in result:
                post_id = result['id']
                logger.info(f"Successfully posted to Facebook. Post ID: {post_id}")
                return post_id
            else:
                logger.error(f"Unexpected response: {result}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error posting to Facebook: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting to Facebook: {e}")
            return None
    
    def post_text(self, message: str) -> Optional[str]:
        """
        Post text-only status to Facebook Page
        
        Args:
            message: Status message
            
        Returns:
            Post ID if successful, None otherwise
        """
        if not self.page_access_token or not self.page_id:
            logger.error("Facebook credentials not configured")
            return None
        
        try:
            logger.info("Posting text status to Facebook")
            
            url = f"{self.base_url}/{self.page_id}/feed"
            
            data = {
                'message': message,
                'access_token': self.page_access_token
            }
            
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'id' in result:
                post_id = result['id']
                logger.info(f"Successfully posted text. Post ID: {post_id}")
                return post_id
            else:
                logger.error(f"Unexpected response: {result}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error posting to Facebook: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting to Facebook: {e}")
            return None
    
    def post_link(self, link: str, message: str = "", picture: str = None) -> Optional[str]:
        """
        Post a link to Facebook Page
        
        Args:
            link: URL to share
            message: Message to accompany the link
            picture: Optional picture URL
            
        Returns:
            Post ID if successful, None otherwise
        """
        if not self.page_access_token or not self.page_id:
            logger.error("Facebook credentials not configured")
            return None
        
        try:
            logger.info(f"Posting link to Facebook: {link}")
            
            url = f"{self.base_url}/{self.page_id}/feed"
            
            data = {
                'link': link,
                'message': message,
                'access_token': self.page_access_token
            }
            
            if picture:
                data['picture'] = picture
            
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'id' in result:
                post_id = result['id']
                logger.info(f"Successfully posted link. Post ID: {post_id}")
                return post_id
            else:
                logger.error(f"Unexpected response: {result}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error posting link to Facebook: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting link: {e}")
            return None
    
    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post from Facebook Page
        
        Args:
            post_id: ID of the post to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.page_access_token:
            logger.error("Facebook credentials not configured")
            return False
        
        try:
            logger.info(f"Deleting post: {post_id}")
            
            url = f"{self.base_url}/{post_id}"
            
            data = {
                'access_token': self.page_access_token
            }
            
            response = requests.delete(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            success = result.get('success', False)
            if success:
                logger.info(f"Successfully deleted post: {post_id}")
            else:
                logger.warning(f"Failed to delete post: {post_id}")
            
            return success
            
        except requests.RequestException as e:
            logger.error(f"Error deleting post: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting post: {e}")
            return False
    
    def get_page_info(self) -> Optional[Dict]:
        """
        Get Facebook Page information
        
        Returns:
            Page info dictionary or None
        """
        if not self.page_access_token or not self.page_id:
            logger.error("Facebook credentials not configured")
            return None
        
        try:
            url = f"{self.base_url}/{self.page_id}"
            
            params = {
                'fields': 'id,name,username,followers_count,likes',
                'access_token': self.page_access_token
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error getting page info: {e}")
            return None
    
    def validate_token(self) -> bool:
        """
        Validate that the access token is working
        
        Returns:
            True if token is valid, False otherwise
        """
        if not self.page_access_token:
            return False
        
        try:
            # Debug token endpoint
            url = f"{self.base_url}/debug_token"
            
            params = {
                'input_token': self.page_access_token,
                'access_token': self.page_access_token
            }
            
            response = requests.get(url, params=params, timeout=30)
            result = response.json()
            
            is_valid = result.get('data', {}).get('is_valid', False)
            
            if is_valid:
                logger.info("Facebook access token is valid")
            else:
                logger.warning("Facebook access token is invalid")
            
            return is_valid
            
        except requests.RequestException as e:
            logger.error(f"Error validating token: {e}")
            return False
    
    def create_complete_post(self, image_path: str, headline: str, 
                           trend_topic: str) -> Dict:
        """
        Create a complete Facebook post with image and caption
        
        Args:
            image_path: Path to news card image
            headline: Generated headline
            trend_topic: Original trend topic
            
        Returns:
            Result dictionary with success status and post_id
        """
        # Build caption
        caption = self._build_caption(headline, trend_topic)
        
        # Post photo with caption
        post_id = self.post_photo(image_path, caption)
        
        return {
            'success': post_id is not None,
            'post_id': post_id,
            'headline': headline,
            'topic': trend_topic,
            'image_path': image_path,
            'posted_at': datetime.utcnow().isoformat()
        }
    
    def _build_caption(self, headline: str, trend_topic: str) -> str:
        """
        Build a Facebook post caption
        
        Args:
            headline: News headline
            trend_topic: Trending topic
            
        Returns:
            Formatted caption
        """
        # Create engaging caption
        caption = f"🔴 {headline}\n\n"
        caption += f"📈 Trending: {trend_topic}\n\n"
        caption += "Stay informed with the latest updates. Follow us for more breaking news! 📰"
        
        return caption


def main():
    """Test the Facebook poster"""
    logging.basicConfig(level=logging.INFO)
    
    poster = FacebookPoster()
    
    if not poster.page_access_token:
        print("Facebook credentials not configured. Set FB_PAGE_ACCESS_TOKEN and FB_PAGE_ID.")
        return
    
    # Validate token
    is_valid = poster.validate_token()
    print(f"Token valid: {is_valid}")
    
    if is_valid:
        # Get page info
        page_info = poster.get_page_info()
        if page_info:
            print(f"Page: {page_info.get('name')} (ID: {page_info.get('id')})")


if __name__ == "__main__":
    main()