"""
Image Processor Module
Creates professional news card images using Pillow with fixed news-outlet template
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
    """Process images to create professional news cards with fixed template"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize image processor
        
        Args:
            output_dir: Directory to save output images
        """
        self.output_dir = output_dir or os.getenv('OUTPUT_DIR', '../output')
        self.canvas_size = (1080, 1080)
        
        # Colors
        self.RED = (220, 30, 35)
        self.DARK_RED = (180, 20, 25)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        
        # Load fonts
        self.font_bold = None
        self.font_regular = None
        self._load_fonts()
        
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Image processor initialized. Output dir: {self.output_dir}")
    
    def _load_fonts(self):
        """Load fonts - DejaVu is installed in Docker for reliability"""
        font_paths = [
            # DejaVu (installed via Docker: fonts-dejavu-core)
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            # Liberation (installed via Docker: fonts-liberation)
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans.ttf",
            # Windows fallback
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                if self.font_bold is None and ('Bold' in path or 'bd' in path.lower()):
                    self.font_bold = path
                elif self.font_regular is None and 'Bold' not in path and 'bd' not in path.lower():
                    self.font_regular = path
        
        # Use bold as regular if no regular found
        if self.font_regular is None:
            self.font_regular = self.font_bold
        
        logger.info(f"Fonts - Bold: {self.font_bold}, Regular: {self.font_regular}")
    
    def _get_font(self, size: int, bold: bool = False):
        """Get font at specified size"""
        path = self.font_bold if bold else self.font_regular
        if path:
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
        return ImageFont.load_default()
    
    def download_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """Download image from URL"""
        if not url:
            return None
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            logger.info(f"Downloaded image: {img.size}")
            return img
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def create_news_card(self, image: Image.Image, headline: str, logo_path: str = None) -> Image.Image:
        """
        Create fixed-format news card with:
        - Full-bleed background image with dark overlay
        - Top: "BREAKING NEWS" red badge
        - Middle: Headline in bold RED text with black outline
        - Bottom: Red accent bar + "FB News" watermark
        """
        w, h = self.canvas_size
        
        # 1. Create canvas
        canvas = Image.new('RGB', (w, h), self.BLACK)
        
        # 2. Resize and paste background image
        img = self._resize_cover(image, (w, h))
        canvas.paste(img, (0, 0))
        
        # 3. Enhance
        canvas = ImageEnhance.Contrast(canvas).enhance(1.1)
        canvas = canvas.filter(ImageFilter.SHARPEN)
        
        # 4. Dark gradient overlay (bottom 60%)
        overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        gradient_start = int(h * 0.35)
        for y in range(gradient_start, h):
            progress = (y - gradient_start) / (h - gradient_start)
            alpha = int(min(progress * 230, 230))
            draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(canvas)
        
        # 5. Top red bar
        draw.rectangle([(0, 0), (w, 6)], fill=self.RED)
        
        # 6. "BREAKING NEWS" badge (top-left)
        badge_text = "BREAKING NEWS"
        badge_font = self._get_font(34, bold=True)
        bb = draw.textbbox((0, 0), badge_text, font=badge_font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        bx, by = 25, 18
        bw, bh = tw + 28, th + 16
        # Red rounded rectangle
        draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=5, fill=self.DARK_RED)
        draw.text((bx + 14, by + (bh - th) // 2 - 1), badge_text, fill=self.WHITE, font=badge_font)
        
        # 7. Headline (bold RED with black outline, very large - centered in bottom area)
        h_font = self._get_font(110, bold=True)
        max_text_w = w - 60
        lines = self._wrap_text(draw, headline, h_font, max_text_w)
        line_h = 130
        total_h = len(lines) * line_h
        
        # Position: centered vertically in the lower 40% of the image
        text_area_top = int(h * 0.60)
        text_y_start = text_area_top + (int(h * 0.35) - total_h) // 2
        
        for i, line in enumerate(lines):
            bb = draw.textbbox((0, 0), line, font=h_font)
            lw = bb[2] - bb[0]
            tx = (w - lw) // 2
            ty = text_y_start + i * line_h
            
            # Black outline (thick) for readability
            for dx, dy in [(-3, -3), (-3, 3), (3, -3), (3, 3), (0, -3), (0, 3), (-3, 0), (3, 0)]:
                draw.text((tx + dx, ty + dy), line, fill=self.BLACK, font=h_font)
            # Red text on top
            draw.text((tx, ty), line, fill=self.RED, font=h_font)
        
        # 8. Red accent bar below headline
        bar_y = int(h * 0.88)
        bar_w = 160
        draw.rectangle([((w - bar_w) // 2, bar_y), ((w + bar_w) // 2, bar_y + 4)], fill=self.RED)
        
        # 9. Watermark
        wm_font = self._get_font(18, bold=True)
        wm_text = "FB News"
        wm_bb = draw.textbbox((0, 0), wm_text, font=wm_font)
        wm_w = wm_bb[2] - wm_bb[0]
        draw.text((w - wm_w - 25, h - 40), wm_text, fill=(200, 16, 26, 180), font=wm_font)
        
        return canvas
    
    def _resize_cover(self, image: Image.Image, target: Tuple[int, int]) -> Image.Image:
        """Resize image to cover target dimensions (center-cropped)"""
        tw, th = target
        iw, ih = image.size
        ratio = max(tw / iw, th / ih)
        nw, nh = int(iw * ratio), int(ih * ratio)
        image = image.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - tw) // 2
        top = (nh - th) // 2
        return image.crop((left, top, left + tw, top + th))
    
    def _wrap_text(self, draw, text: str, font, max_width: int) -> list:
        """Wrap text to fit within max_width, max 3 lines"""
        words = text.split()
        lines = []
        cur = ""
        for word in words:
            test = (cur + " " + word).strip()
            bb = draw.textbbox((0, 0), test, font=font)
            if bb[2] - bb[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        if len(lines) > 3:
            lines = lines[:3]
            if lines:
                lines[-1] = lines[-1].rstrip('.') + "..."
        return lines if lines else [text]
    
    def save_image(self, image: Image.Image, filename: str = None) -> str:
        """Save image to output directory"""
        if filename is None:
            filename = f"news_card_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)
        image.save(path, 'JPEG', quality=92, optimize=True)
        logger.info(f"Saved: {path}")
        return path
    
    def process_from_url(self, image_url: str, headline: str, logo_path: str = None) -> Optional[str]:
        """Download image, create news card, save"""
        image = self.download_image(image_url)
        if not image:
            return None
        card = self.create_news_card(image, headline, logo_path)
        return self.save_image(card)


def main():
    logging.basicConfig(level=logging.INFO)
    p = ImageProcessor()
    url = "https://picsum.photos/seed/news123/800/600.jpg"
    h = "Major Policy Changes Announced Today by Government Officials"
    r = p.process_from_url(url, h)
    print(f"Created: {r}")


if __name__ == "__main__":
    main()