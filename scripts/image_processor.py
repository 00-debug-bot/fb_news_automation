"""
Image Processor Module
Creates professional news card images using Pillow
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
    """Process images to create professional news cards"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize image processor
        
        Args:
            output_dir: Directory to save output images
        """
        self.output_dir = output_dir or os.getenv('OUTPUT_DIR', '../output')
        self.canvas_size = (1080, 1080)
        
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
            # Linux fonts
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
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
                if 'Bold' in path or 'bd' in path.lower():
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
            
            # Convert to RGB if necessary (handle PNG with transparency, etc.)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
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
        Create a professional news card from an image
        
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
        canvas = enhancer.enhance(1.1)
        
        # Add slight sharpening
        canvas = canvas.filter(ImageFilter.SHARPEN)
        
        # Create gradient overlay
        overlay = self._create_gradient_overlay(self.canvas_size)
        canvas = Image.alpha_composite(canvas.convert('RGBA'), overlay)
        
        # Convert back to RGB
        canvas = canvas.convert('RGB')
        
        # Add BREAKING label
        canvas = self._add_breaking_label(canvas)
        
        # Add headline
        canvas = self._add_headline(canvas, headline)
        
        # Add logo/watermark
        if logo_path and os.path.exists(logo_path):
            canvas = self._add_watermark(canvas, logo_path)
        else:
            # Add text watermark
            canvas = self._add_text_watermark(canvas, "FB News")
        
        # Add subtle vignette effect
        canvas = self._add_vignette(canvas)
        
        return canvas
    
    def _resize_cover(self, image: Image.Image, 
                     target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize image to cover target size (like CSS object-fit: cover)
        
        Args:
            image: Source image
            target_size: Target dimensions
            
        Returns:
            Resized image
        """
        target_w, target_h = target_size
        img_w, img_h = image.size
        
        # Calculate aspect ratios
        img_ratio = img_w / img_h
        target_ratio = target_w / target_h
        
        if img_ratio > target_ratio:
            # Image is wider, fit to height
            new_h = target_h
            new_w = int(new_h * img_ratio)
        else:
            # Image is taller, fit to width
            new_w = target_w
            new_h = int(new_w / img_ratio)
        
        # Resize
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Center crop
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        right = left + target_w
        bottom = top + target_h
        
        image = image.crop((left, top, right, bottom))
        
        return image
    
    def _create_gradient_overlay(self, size: Tuple[int, int]) -> Image.Image:
        """
        Create a dark gradient overlay for the bottom portion
        
        Args:
            size: Canvas size
            
        Returns:
            RGBA overlay image
        """
        overlay = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        w, h = size
        
        # Gradient from transparent (top) to dark (bottom)
        # Start gradient at 50% height
        gradient_start = int(h * 0.45)
        
        # Create gradient with multiple stops
        for y in range(gradient_start, h):
            # Calculate alpha (0 to ~200)
            progress = (y - gradient_start) / (h - gradient_start)
            alpha = int(progress * 200)
            
            # Dark blue-black color for professional look
            color = (10, 15, 30, alpha)
            draw.line([(0, y), (w, y)], fill=color)
        
        return overlay
    
    def _add_breaking_label(self, image: Image.Image) -> Image.Image:
        """
        Add a red BREAKING label to top-left
        
        Args:
            image: Source image
            
        Returns:
            Image with label
        """
        draw = ImageDraw.Draw(image)
        w, h = image.size
        
        # Label settings
        label_text = "BREAKING"
        font_size = 36
        font = self._get_font(font_size, bold=True)
        
        # Get text size
        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Padding
        padding = 20
        label_w = text_w + padding * 2
        label_h = text_h + padding
        
        # Position (top-left with margin)
        margin = 30
        label_x = margin
        label_y = margin
        
        # Draw red background
        draw.rectangle(
            [(label_x, label_y), (label_x + label_w, label_y + label_h)],
            fill=(220, 20, 20)  # Red
        )
        
        # Draw text
        text_x = label_x + padding
        text_y = label_y + (label_h - text_h) // 2
        draw.text((text_x, text_y), label_text, fill=(255, 255, 255), font=font)
        
        return image
    
    def _add_headline(self, image: Image.Image, headline: str) -> Image.Image:
        """
        Add headline text to the lower portion
        
        Args:
            image: Source image
            headline: Headline text
            
        Returns:
            Image with headline
        """
        draw = ImageDraw.Draw(image)
        w, h = image.size
        
        # Settings
        font_size = 52
        font = self._get_font(font_size, bold=True)
        
        # Text color with slight shadow for readability
        text_color = (255, 255, 255)
        shadow_color = (0, 0, 0)
        
        # Wrap text if needed
        max_width = w - 80
        lines = self._wrap_text(draw, headline, font, max_width)
        
        # Calculate total text height
        line_height = font_size * 1.3
        total_text_h = len(lines) * line_height
        
        # Position (lower third, centered)
        text_y_start = int(h * 0.65)
        
        # Draw each line with shadow
        for i, line in enumerate(lines):
            # Get line dimensions
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            
            # Center horizontally
            text_x = (w - line_w) // 2
            text_y = text_y_start + i * line_height
            
            # Draw shadow (slightly offset)
            draw.text((text_x + 2, text_y + 2), line, fill=shadow_color, 
                     font=font, stroke_width=1)
            
            # Draw main text
            draw.text((text_x, text_y), line, fill=text_color, font=font)
        
        return image
    
    def _wrap_text(self, draw: ImageDraw.ImageDraw, text: str, 
                  font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """
        Wrap text to fit within max width
        
        Args:
            draw: ImageDraw object
            text: Text to wrap
            font: Font to use
            max_width: Maximum width
            
        Returns:
            List of wrapped lines
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
            # Add ellipsis to last line if truncated
            if lines:
                lines[-1] = lines[-1] + "..."
        
        return lines if lines else [text]
    
    def _add_watermark(self, image: Image.Image, logo_path: str) -> Image.Image:
        """
        Add logo watermark to bottom-right
        
        Args:
            image: Source image
            logo_path: Path to logo file
            
        Returns:
            Image with watermark
        """
        try:
            logo = Image.open(logo_path)
            
            # Convert to RGBA for transparency
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Resize logo
            logo_size = (120, 120)
            logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
            
            # Position (bottom-right with margin)
            margin = 30
            x = image.width - logo_size[0] - margin
            y = image.height - logo_size[1] - margin
            
            # Make logo semi-transparent
            logo = Image.blend(logo, Image.new('RGBA', logo_size, (0, 0, 0, 0)), 0.3)
            
            # Paste with mask
            image_rgba = image.convert('RGBA')
            image_rgba.paste(logo, (x, y), logo)
            
            return image_rgba.convert('RGB')
            
        except Exception as e:
            logger.warning(f"Could not add logo watermark: {e}")
            return image
    
    def _add_text_watermark(self, image: Image.Image, text: str) -> Image.Image:
        """
        Add text watermark to bottom-right
        
        Args:
            image: Source image
            text: Watermark text
            
        Returns:
            Image with watermark
        """
        draw = ImageDraw.Draw(image)
        
        font_size = 18
        font = self._get_font(font_size)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        
        margin = 30
        x = image.width - text_w - margin
        y = image.height - font_size - margin
        
        # Semi-transparent white
        draw.text((x, y), text, fill=(255, 255, 255, 128), font=font)
        
        return image
    
    def _add_vignette(self, image: Image.Image, intensity: float = 0.3) -> Image.Image:
        """
        Add subtle vignette effect
        
        Args:
            image: Source image
            intensity: Vignette intensity
            
        Returns:
            Image with vignette
        """
        w, h = image.size
        
        # Create radial gradient
        overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Calculate center
        cx, cy = w // 2, h // 2
        
        # Calculate max distance from center
        max_dist = ((cx ** 2 + cy ** 2) ** 0.5)
        
        # Draw vignette (darker edges)
        for y in range(h):
            for x in range(w):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                progress = dist / max_dist
                
                if progress > 0.4:
                    alpha = int((progress - 0.4) * intensity * 255 * (1 - 0.4) / 0.6)
                    alpha = min(alpha, 100)  # Cap at 100
                    draw.point((x, y), fill=(0, 0, 0, alpha))
        
        # Blend overlay
        result = Image.alpha_composite(image.convert('RGBA'), overlay)
        return result.convert('RGB')
    
    def save_image(self, image: Image.Image, filename: str = None) -> str:
        """
        Save image to output directory
        
        Args:
            image: PIL Image to save
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"news_card_{timestamp}.jpg"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save as high-quality JPEG
        image.save(filepath, 'JPEG', quality=95, optimize=True)
        
        logger.info(f"Saved image to: {filepath}")
        return filepath
    
    def process_from_url(self, image_url: str, headline: str, 
                        logo_path: str = None) -> Optional[str]:
        """
        Complete workflow: download image and create news card
        
        Args:
            image_url: URL of source image
            headline: Headline text
            logo_path: Optional logo path
            
        Returns:
            Path to saved news card or None
        """
        # Download image
        image = self.download_image(image_url)
        if not image:
            logger.error("Failed to download image")
            return None
        
        # Create news card
        news_card = self.create_news_card(image, headline, logo_path)
        
        # Save
        filepath = self.save_image(news_card)
        return filepath


def main():
    """Test the image processor"""
    logging.basicConfig(level=logging.INFO)
    
    processor = ImageProcessor(output_dir="../output")
    
    # Test with a sample image URL
    test_url = "https://picsum.photos/seed/news123/800/600.jpg"
    test_headline = "Major Policy Changes Announced Today"
    
    print("Processing test image...")
    result = processor.process_from_url(test_url, test_headline)
    
    if result:
        print(f"News card created: {result}")
    else:
        print("Failed to create news card")


if __name__ == "__main__":
    main()