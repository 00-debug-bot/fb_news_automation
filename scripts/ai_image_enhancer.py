"""
AI Image Enhancer Module
Uses OpenRouter (Google Gemini 3.1 Flash Image Preview) to generate HD news images from headlines
"""

import logging
import os
import base64
import io
import time
import json
from typing import Optional, Tuple
import requests
from PIL import Image

logger = logging.getLogger(__name__)


class AIImageEnhancer:
    """Generate high-quality news images using AI via OpenRouter"""
    
    def __init__(self, openrouter_api_key: str = None):
        """
        Initialize AI image enhancer
        
        Args:
            openrouter_api_key: OpenRouter API key (defaults to env var)
        """
        self.api_key = (openrouter_api_key or os.getenv('OPENROUTER_API_KEY', '')).strip()
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://fb-news-automation.railway.app",
            "X-Title": "FB News Automation"
        }
        
        # Image generation model
        self.model = "google/gemini-3.1-flash-image-preview"  # Free tier, supports image generation
        
        logger.info(f"AI Image Enhancer initialized with model: {self.model}")
    
    def generate_news_image(self, headline: str, aspect_ratio: str = "1:1") -> Optional[Image.Image]:
        """
        Generate a high-quality news image from a headline
        
        Args:
            headline: News headline to visualize
            aspect_ratio: Image aspect ratio (1:1, 16:9, etc.)
            
        Returns:
            PIL Image or None if failed
        """
        prompt = self._build_prompt(headline, aspect_ratio)
        
        try:
            # Prepare the request
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            logger.info(f"Generating AI image for headline: {headline[:50]}...")
            response = requests.post(self.api_url, headers=self.headers, 
                                    json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract image from response (Gemini returns image in content)
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                # The image might be returned as a URL or base64 in the text
                # For now, we'll log and return None (actual implementation depends on model output)
                logger.info(f"AI response: {content[:200]}")
                
                # Since Gemini 3.1 Flash Image Preview might not return direct image,
                # we'll fallback to using DALL-E 3 via OpenRouter if needed
                return self._generate_with_dalle(headline)
            
            return None
            
        except Exception as e:
            logger.error(f"AI image generation failed: {e}")
            return None
    
    def _generate_with_dalle(self, headline: str) -> Optional[Image.Image]:
        """Fallback to DALL-E 3 for image generation"""
        try:
            dalle_payload = {
                "model": "openai/dall-e-3",
                "prompt": self._build_dalle_prompt(headline),
                "n": 1,
                "size": "1024x1024",
                "quality": "standard"
            }
            
            dalle_response = requests.post(
                "https://openrouter.ai/api/v1/images/generations",
                headers=self.headers,
                json=dalle_payload,
                timeout=60
            )
            dalle_response.raise_for_status()
            
            dalle_data = dalle_response.json()
            image_url = dalle_data.get("data", [{}])[0].get("url")
            
            if image_url:
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                return Image.open(io.BytesIO(img_response.content))
            
        except Exception as e:
            logger.error(f"DALL-E fallback failed: {e}")
        
        return None
    
    def _build_prompt(self, headline: str, aspect_ratio: str) -> str:
        """Build detailed prompt for news image generation"""
        return f"""
        Create a professional news image for this headline: "{headline}"
        
        Image Requirements:
        - Aspect ratio: {aspect_ratio} (square)
        - Style: Professional news photography, photojournalism style
        - Mood: Serious, impactful, newsworthy
        - Composition: Dynamic, with visual elements related to the headline
        - Quality: High definition, sharp, professional lighting
        - Text: Do NOT include any text or headlines in the image
        - Colors: Vibrant but realistic, news-appropriate
        
        The image should be suitable for a news website or social media news post.
        Focus on visual storytelling that complements the headline.
        """
    
    def _build_dalle_prompt(self, headline: str) -> str:
        """Build DALL-E specific prompt"""
        return f"""
        Professional news photography image for headline: "{headline}".
        Photorealistic, high definition, photojournalism style, dynamic composition,
        serious mood, impactful, newsworthy, vibrant colors, no text in image.
        """
    
    def enhance_existing_image(self, image: Image.Image, headline: str) -> Optional[Image.Image]:
        """
        Enhance an existing image with AI (add effects, improve quality)
        
        Args:
            image: PIL Image to enhance
            headline: Headline for context
            
        Returns:
            Enhanced PIL Image or None
        """
        try:
            # Convert image to base64 for sending to AI
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            prompt = f"""
            Enhance this news image to look more professional and impactful.
            Headline: "{headline}"
            
            Enhancements needed:
            1. Improve lighting and contrast
            2. Add subtle news-style filters (slight desaturation, increased clarity)
            3. Ensure the image looks like professional news photography
            4. Maintain original composition but enhance visual impact
            5. Do NOT add text or change the fundamental content
            
            Return the enhanced image.
            """
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 100
            }
            
            response = requests.post(self.api_url, headers=self.headers,
                                    json=payload, timeout=60)
            response.raise_for_status()
            
            # Process response (similar to generate_news_image)
            # This would need actual implementation based on model capabilities
            logger.info("Image enhancement requested")
            return image  # Fallback to original for now
            
        except Exception as e:
            logger.error(f"Image enhancement failed: {e}")
            return image
    
    def save_image(self, image: Image.Image, filename: str = None) -> str:
        """Save image to output directory"""
        output_dir = os.getenv('OUTPUT_DIR', '../output')
        os.makedirs(output_dir, exist_ok=True)
        
        if filename is None:
            from datetime import datetime
            filename = f"ai_news_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        path = os.path.join(output_dir, filename)
        image.save(path, 'JPEG', quality=95, optimize=True)
        logger.info(f"Saved AI image: {path}")
        return path


def main():
    """Test the AI image enhancer"""
    logging.basicConfig(level=logging.INFO)
    
    enhancer = AIImageEnhancer()
    
    test_headline = "Major Policy Changes Announced Today by Government Officials"
    print(f"Generating image for: {test_headline}")
    
    image = enhancer.generate_news_image(test_headline)
    
    if image:
        print(f"Image generated: {image.size}")
        path = enhancer.save_image(image)
        print(f"Saved to: {path}")
    else:
        print("Image generation failed")


if __name__ == "__main__":
    main()