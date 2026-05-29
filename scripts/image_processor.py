"""
Image Processor Module
Creates professional news card images using Pillow with news-outlet style design
"""

import logging
import os
import io
import requests
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from datetime import datetime

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process images to create professional news cards with news-outlet styling"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize image processor
        
        Args:
            output_dir: Directory to save output images
        """
        self.output_dir = output_dir or os.getenv('OUTPUT_DIR', '../output')
        self.canvas_size = (1080, 1080)
        
        # News-outlet brand colors
        self.RED = (200, 16, 26)       # Bold news red
        self.DARK_RED = (150, 10, 18)   # Darker red for accents
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.DARK_BG = (10, 10, 15)     # Near-black for overlays
        
        # Try to load fonts
        self._load_fonts()
        
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Image processor initialized. Output dir: {self.output_dir}")
    
    def _load_fonts(self):
        """Load fonts for text rendering"""
        # Try common font paths
        font_paths = [
            # Windows fonts
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arialbi.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "C:/Windows/Fonts/impact.ttf",
            # Linux fonts
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            # Mac fonts
            "/Library/Fonts/Arial.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            # Fallback - will use default if none found
        ]
        
        self.font_regular = None
        self.font_bold = None
        self.font_black = None
        
        for path in font_paths:
            if os.path.exists(path):
                if 'Bold' in path or 'bd' in path.lower() or 'timesbd' in path.lower():
                    if not self.font_bold:
                        self.font_bold = path
                elif not self.font_regular:
                    self.font_regular = path
        
        # If no bold font found, use regular
        if not self.font_bold:
            self.font_bold = self.font_regular
        
        logger.info(f"Fonts loaded - Regular: {self.font_regular}, Bold: {self.font_bold}")
    
    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """
        Get a font of specified size
        
        Args:
            size: Font size
            bold: Whether to use bold font
            
        Returns:
            PIL ImageFont
        """
        font_path = self.font_bold if bold else self.font_regular
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        
        # Fallback to default font
        try:
            return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()
    
    def download_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """
        Download an image from URL
        
        Args:
            url: Image URL
            timeout: Request timeout
            
        Returns:
            PIL Image or None
        """
        if not url:
            logger.warning("No image URL provided")
            return None
        
        try:
            logger.info(f"Downloading image from: {url[:80]}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            logger.info(f"Downloaded image: {image.size}")
            return image
            
        except requests.RequestException as e:
            logger.error(f"Error downloading image: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing downloaded image: {e}")
            return None
    
    def create_news_card(self, image: Image.Image, headline: str, 
                        logo_path: str = None) -> Image.Image:
        """
        Create a professional news card from an image with news-outlet style
        
        Args:
            image: Source PIL Image
            headline: Headline text to overlay
            logo_path: Path to logo/watermark image
            
        Returns:
            Processed PIL Image
        """
        # Start with a black canvas
        canvas = Image.new('RGB', self.canvas_size, (0, 0, 0))
        
        # Resize and crop image to fit canvas (cover mode)
        image = self._resize_cover(image, self.canvas_size)
        
        # Place image centered
        x_offset = (self.canvas_size[0] - image.width) // 2
        y_offset = (self.canvas_size[1] - image.height) // 2
        canvas.paste(image, (x_offset, y_offset))
        
        # Enhance contrast slightly
        enhancer = ImageEnhance.Contrast(canvas)
        canvas = enhancer.enhance(1.15)
        
        # Add slight sharpening
        canvas = canvas.filter(ImageFilter.SHARPEN)
        
        # Create dark gradient overlay for bottom text area
        overlay = self._create_news_overlay(self.canvas_size)
        canvas = Image.alpha_composite(canvas.convert('RGBA'), overlay)
        
        # Convert back to RGB
        canvas = canvas.convert('RGB')
        
        # Add top red bar (news channel style)
        canvas = self._add_top_red_bar(canvas)
        
        # Add BREAKING label
        canvas = self._add_breaking_label(canvas)
        
        # Add headline in RED
        canvas = self._add_headline(canvas, headline)
        
        # Add red accent line below headline
        canvas = self._add_red_accent_line(canvas)
        
        # Add logo/watermark
        if logo_path and os.path.exists(logo_path):
            canvas = self._add_watermark(canvas, logo_path)
        else:
            canvas = self._add_text_watermark(canvas, "FB News")
        
        # Add subtle vignette effect
        canvas = self._add_vignette(canvas)
        
        return canvas
    
    def _resize_cover(self, image: Image.Image, 
                     target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize image to cover target size (like CSS object-fit: cover)
        """
        target_w, target_h = target_size
        img_w, img_h = image.size
        
        img_ratio = img_w / img_h
        target_ratio = target_w / target_h
        
        if img_ratio > target_ratio:
            new_h = target_h
            new_w = int(new_h * img_ratio)
        else:
            new_w = target_w
            new_h = int(new_w / img_ratio)
        
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        right = left + target_w
        bottom = top + target_h
        
        image = image.crop((left, top, right, bottom))
        
        return image
    
    def _create_news_overlay(self, size: Tuple[int, int]) -> Image.Image:
        """
        Create a professional dark gradient overlay with extra darkness at bottom
        """
        overlay = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        w, h = size
        
        # Start gradient earlier for news style - at 35%
        gradient_start = int(h * 0.35)
        
        # Create gradient that gets darker towards bottom
        for y in range(gradient_start, h):
            progress = (y - gradient_start) / (h - gradient_start)
            # More aggressive darkening
            alpha = int(progress * 220)
            color = (0, 0, 0, alpha)
            draw.line([(0, y), (w, y)], fill=color)
        
        # Add a dark strip at the very bottom for extra contrast
        bottom_strip_start = int(h * 0.82)
        for y in range(bottom_strip_start, h):
            alpha = 180 + int(((y - bottom_strip_start) / (h - bottom_strip_start)) * 75)
            alpha = min(alpha, 255)
            draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
        
        return overlay
    
    def _add_top_red_bar(self, image: Image.Image) -> Image.Image:
        """Add a red bar at the very top of the image (news channel style)"""
        draw = ImageDraw.Draw(image)
        w, _ = image.size
        
        # Thin red line at very top
        bar_height = 5
        draw.rectangle([(0, 0), (w, bar_height)], fill=self.RED)
        
        return image
    
    def _add_breaking_label(self, image: Image.Image) -> Image.Image:
        """
        Add a red BREAKING label to top-left
        """
        draw = ImageDraw.Draw(image)
        w, h = image.size
        
        label_text = "BREAKING NEWS"
        font_size = 40
        font = self._get_font(font_size, bold=True)
        
        # Get text size
        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Padding
        padding_h = 16
        padding_v = 10
        label_w = text_w + padding_h * 2
        label_h = text_h + padding_v * 2
        
        # Position (top-left with margin)
        margin = 25
        label_x = margin
        label_y = margin + 15  # Below the red top bar
        
        # Draw red background rectangle
        draw.rounded_rectangle(
            [(label_x, label_y), (label_x + label_w, label_y + label_h)],
            radius=4,
            fill=self.RED
        )
        
        # Draw white text
        text_x = label_x + padding_h
        text_y = label_y + padding_v
        draw.text((text_x, text_y), label_text, fill=self.WHITE, font=font)
        
        return image
    
    def _add_headline(self, image: Image.Image, headline: str) -> Image.Image:
        """
        Add headline text in RED color (news-outlet style) at the bottom portion
        """
        draw = ImageDraw.Draw(image)
        w, h = image.size
        
        # LARGE font size for easy reading
        font_size = 62
        font = self._get_font(font_size, bold=True)
        
        # Text color: RED for news outlet feel
        text_color = (220, 30, 35)  # Vivid red
        shadow_color = (0, 0, 0)
        
        # Wrap text if needed
        max_width = w - 100
        lines = self._wrap_text(draw, headline, font, max_width)
        
        # Line spacing
        line_height = int(font_size * 1.4)
        total_text_h = len(lines) * line_height
        
        # Position in lower portion (around 65-70% down)
        text_y_start = int(h * 0.65)
        
        # Draw each line with shadow for readability
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            
            # Center horizontally
            text_x = (w - line_w) // 2
            text_y = text_y_start + i * line_height
            
            # Draw thick black shadow/outline for readability
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, 2), (0, -2), (2, 0), (-2, 0)]:
                draw.text((text_x + dx, text_y + dy), line, fill=shadow_color, font=font)
            
            # Draw main RED text on top
            draw.text((text_x, text_y), line, fill=text_color, font=font)
        
        return image
    
    def _add_red_accent_line(self, image: Image.Image) -> Image.Image:
        """
        Add a red accent line below the headline (news channel style)
        """
        draw = ImageDraw.Draw(image)
        w, h = image.size
        
        # Position below headline area (around 88% down)
        line_y = int(h * 0.88)
        line_width = 4
        line_length = 200
        
        # Center the accent line
        line_x_start = (w - line_length) // 2
        line_x_end = line_x_start + line_length
        
        # Draw red accent line
        draw.rectangle(
            [(line_x_start, line_y), (line_x_end, line_y + line_width)],
            fill=self.RED
        )
        
        return image
    
    def _wrap_text(self, draw: ImageDraw.ImageDraw, text: str, 
                  font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """
        Wrap text to fit within max width
        """
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Limit to 3 lines max
        if len(lines) > 3:
            lines = lines[:3]
            if lines:
                lines[-1] = lines[-1] + "..."
        
        return lines if lines else [text]
    
    def _add_watermark(self, image: Image.Image, logo_path: str) -> Image.Image:
        """Add logo watermark to bottom-right"""
        try:
            logo = Image.open(logo_path)
            
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            logo_size = (100, 100)
            logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
            
            margin = 25
            x = image.width - logo_size[0] - margin
            y = image.height - logo_size[1] - margin - 30
            
            logo = Image.blend(logo, Image.new('RGBA', logo_size, (0, 0, 0, 0)), 0.3)
            
            image_rgba = image.convert('RGBA')
            image_rgba.paste(logo, (x, y), logo)
            
            return image_rgba.convert('RGB')
            
        except Exception as e:
            logger.warning(f"Could not add logo watermark: {e}")
            return image
    
    def _add_text_watermark(self, image: Image.Image, text: str) -> Image.Image:
        """
        Add text watermark to bottom-right
        """
        draw = ImageDraw.Draw(image)
        
        font_size = 20
        font = self._get_font(font_size, bold=True)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        
        margin = 25
        x = image.width - text_w - margin
        y = image.height - font_size - margin - 30
        
        # Semi-transparent red watermark
        draw.text((x, y), text, fill=(200, 16, 26, 180), font=font)
        
        return image
    
    def _add_vignette(self, image: Image.Image) -> Image.Image:
        """
        Add subtle vignette effect
        """
        w, h = image.size
        
        overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        cx, cy = w // 2, h // 2
        max_dist = ((cx ** 2 + cy ** 2) ** 0.5)
        
        for y in range(h):
            for x in range(w):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                progress = dist / max_dist
                
                if progress > 0.4:
                    alpha = int((progress - 0.4) * 0.25 * 255 * (1 - 0.4) / 0.6)
                    alpha = min(alpha, 80)
                    draw.point((x, y), fill=(0, 0, 0, alpha))
        
        result = Image.alpha_composite(image.convert('RGBA'), overlay)
        return result.convert('RGB')
    
    def save_image(self, image: Image.Image, filename: str = None) -> str:
        """
        Save image to output directory
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"news_card_{timestamp}.jpg"
        
        filepath = os.path.join(self.output_dir, filename)
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save as high-quality JPEG
        image.save(filepath, 'JPEG', quality=95, optimize=True)
        
        logger.info(f"Saved image to: {filepath}")
        return filepath
    
    def process_from_url(self, image_url: str, headline: str, 
                        logo_path: str = None) -> Optional[str]:
        """
        Complete workflow: download image and create news card
        """
        image = self.download_image(image_url)
        if not image:
            logger.error("Failed to download image")
            return None
        
        news_card = self.create_news_card(image, headline, logo_path)
        filepath = self.save_image(news_card)
        return filepath


def main():
    """Test the image processor"""
    logging.basicConfig(level=logging.INFO)
    
    processor = ImageProcessor(output_dir="../output")
    
    test_url = "https://picsum.photos/seed/news123/800/600.jpg"
    test_headline = "Major Policy Changes Announced Today by Government Officials"
    
    print("Processing test image...")
    result = processor.process_from_url(test_url, test_headline)
    
    if result:
        print(f"News card created: {result}")
    else:
        print("Failed to create news card")


if __name__ == "__main__":
    main()