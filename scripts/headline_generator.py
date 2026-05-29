"""
Headline Generator Module
Uses OpenRouter free models to generate engaging news headlines
"""

import logging
import json
import os
import requests
from typing import Optional, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class HeadlineGenerator:
    """Generate news headlines using OpenRouter AI"""
    
    def __init__(self, api_key: str = None, model: str = None, backup_model: str = None):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY environment variable)
            model: Model to use (default: google/gemma-7b-it:free)
            backup_model: Backup model (default: mistralai/mistral-7b-instruct:free)
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.model = model or os.getenv('OPENROUTER_MODEL', 'google/gemma-7b-it:free')
        self.backup_model = backup_model or os.getenv('OPENROUTER_BACKUP_MODEL', 'mistralai/mistral-7b-instruct:free')
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            logger.warning("OpenRouter API key not provided. Headline generation will be limited.")
        else:
            logger.info(f"OpenRouter client initialized with model: {model}")
    
    def _get_prompt(self, trend_topic: str, article_title: str, 
                    article_description: str) -> str:
        """
        Build the prompt for headline generation
        
        Args:
            trend_topic: The trending topic
            article_title: Article title
            article_description: Article description
            
        Returns:
            Formatted prompt string
        """
        prompt = """You are a professional American social media news editor.

Write ONE short, highly engaging, natural-sounding breaking news headline for Facebook.

Requirements:
- Maximum 14 words
- Sound human-written
- Sound like major US news pages
- Avoid obvious AI wording
- Avoid emojis
- Avoid hashtags
- Create curiosity and urgency
- Do not exaggerate fake facts
- Focus on clicks and impressions
- American audience tone

Trending Topic:
{trend_topic}

Article Title:
{article_title}

Article Description:
{article_description}

Return ONLY the final headline.""".format(
            trend_topic=trend_topic,
            article_title=article_title,
            article_description=article_description
        )
        
        return prompt
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception_type(requests.RequestException)
    )
    def _call_openrouter_api(self, model_name: str, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/fb-news-automation",
            "X-Title": "FB News Automation"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional American social media news editor. Generate only the headline, nothing else."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 60,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        response.raise_for_status()
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content'].strip()
        raise Exception("No choices in response")

    def generate_headline(self, trend_topic: str, article_title: str,
                         article_description: str) -> Optional[str]:
        """
        Generate a news headline using OpenRouter
        
        Args:
            trend_topic: The trending topic
            article_title: Article title
            article_description: Article description
            
        Returns:
            Generated headline or None
        """
        if not self.api_key:
            logger.error("OpenRouter API key not configured")
            return self._fallback_headline(trend_topic, article_title)
        
        prompt = self._get_prompt(trend_topic, article_title, article_description)
        
        # Try primary model
        try:
            logger.info(f"Generating headline with primary model ({self.model}) for: {trend_topic}")
            raw_headline = self._call_openrouter_api(self.model, prompt)
            headline = self._clean_headline(raw_headline)
            logger.info(f"Generated headline: {headline}")
            return headline
        except requests.RequestException as e:
            logger.warning(f"Primary model failed ({e}). Trying backup model: {self.backup_model}")
        except Exception as e:
            logger.warning(f"Primary model failed ({e}). Trying backup model: {self.backup_model}")
            
        # Try backup model
        try:
            raw_headline = self._call_openrouter_api(self.backup_model, prompt)
            headline = self._clean_headline(raw_headline)
            logger.info(f"Generated backup headline: {headline}")
            return headline
        except Exception as e:
            logger.error(f"Backup model also failed: {e}")
            return self._fallback_headline(trend_topic, article_title)
    
    def _clean_headline(self, headline: str) -> str:
        """
        Clean up the generated headline
        
        Args:
            headline: Raw generated headline
            
        Returns:
            Cleaned headline
        """
        # Remove quotes if present
        headline = headline.strip('"\'')
        
        # Remove any "Here's" or similar AI-isms
        ai_phrases = [
            "Here's a headline:",
            "Here is a headline:",
            "Headline:",
            "Breaking:",
            "Here you go:",
            "Sure, here's a headline:"
        ]
        for phrase in ai_phrases:
            if headline.startswith(phrase):
                headline = headline[len(phrase):].strip()
        
        # Remove emojis
        emojis = set(
            char for char in headline
            if '\U0001F600' <= char <= '\U0001F64F' or
               '\U0001F300' <= char <= '\U0001F5FF' or
               '\U0001F680' <= char <= '\U0001F6FF' or
               '\U0001F1E0' <= char <= '\U0001F1FF' or
               '\U00002702' <= char <= '\U000027B0' or
               '\U000024C2' <= char <= '\U0001F251'
        )
        for emoji in emojis:
            headline = headline.replace(emoji, '')
        
        # Remove hashtags
        headline = ' '.join(word for word in headline.split() if not word.startswith('#'))
        
        # Ensure max 14 words
        words = headline.split()
        if len(words) > 14:
            headline = ' '.join(words[:14])
            # Try to end at a natural break
            if ',' in headline:
                last_comma = headline.rfind(',')
                headline = headline[:last_comma]
        
        # Clean up extra whitespace
        headline = ' '.join(headline.split())
        
        return headline
    
    def _fallback_headline(self, trend_topic: str, article_title: str) -> str:
        """
        Generate a fallback headline without AI
        
        Args:
            trend_topic: Trending topic
            article_title: Article title
            
        Returns:
            Fallback headline
        """
        logger.info("Using fallback headline generation")
        
        # Use article title as base, make it shorter if needed
        if article_title:
            words = article_title.split()
            if len(words) > 12:
                headline = ' '.join(words[:12])
            else:
                headline = article_title
        else:
            # Use trend topic
            headline = f"Breaking: {trend_topic} - Latest Updates"
        
        # Add "Breaking" prefix if not already present
        if not headline.lower().startswith(('breaking', 'live', 'update', 'developing')):
            headline = f"Breaking: {headline}"
        
        return self._clean_headline(headline)
    
    def generate_multiple_options(self, trend_topic: str, article_title: str,
                                  article_description: str, count: int = 3) -> list:
        """
        Generate multiple headline options
        
        Args:
            trend_topic: Trending topic
            article_title: Article title
            article_description: Article description
            count: Number of options to generate
            
        Returns:
            List of headline options
        """
        headlines = []
        
        for i in range(count):
            # Add slight variation to prompt for diversity
            variation_prompt = f"{article_description}\n\nAdditional context: Focus on the most impactful aspect."
            
            headline = self.generate_headline(
                trend_topic, 
                article_title, 
                variation_prompt
            )
            
            if headline and headline not in headlines:
                headlines.append(headline)
        
        return headlines
    
    def validate_headline(self, headline: str) -> Dict[str, any]:
        """
        Validate a headline meets requirements
        
        Args:
            headline: Headline to validate
            
        Returns:
            Validation results dictionary
        """
        results = {
            'valid': True,
            'issues': [],
            'word_count': len(headline.split()),
            'character_count': len(headline)
        }
        
        # Check word count
        if results['word_count'] > 14:
            results['valid'] = False
            results['issues'].append(f"Too many words: {results['word_count']}/14")
        
        # Check for emojis
        if any(ord(char) > 127 for char in headline):
            results['issues'].append("Contains non-ASCII characters (possible emojis)")
        
        # Check for hashtags
        if '#' in headline:
            results['issues'].append("Contains hashtags")
            results['valid'] = False
        
        # Check for empty
        if not headline.strip():
            results['valid'] = False
            results['issues'].append("Empty headline")
        
        # Check for minimum length
        if results['word_count'] < 3:
            results['issues'].append("Very short headline")
        
        return results


def main():
    """Test the headline generator"""
    logging.basicConfig(level=logging.INFO)
    
    generator = HeadlineGenerator()
    
    test_cases = [
        {
            'trend': 'Government Shutdown',
            'title': 'Congress Fails to Pass Budget Bill as Deadline Looms',
            'description': 'Lawmakers remain deadlocked over spending priorities as a government shutdown appears increasingly likely.'
        },
        {
            'trend': 'Tech Layoffs',
            'title': 'Major Tech Company Announces 10,000 Job Cuts',
            'description': 'The company cited economic uncertainty and overhiring during the pandemic as reasons for the massive layoffs.'
        }
    ]
    
    for test in test_cases:
        print(f"\nGenerating headline for: {test['trend']}")
        headline = generator.generate_headline(
            test['trend'],
            test['title'],
            test['description']
        )
        print(f"Headline: {headline}")
        
        validation = generator.validate_headline(headline)
        print(f"Validation: {json.dumps(validation, indent=2)}")


if __name__ == "__main__":
    main()