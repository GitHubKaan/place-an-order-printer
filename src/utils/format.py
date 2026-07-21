from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from src.utils.config import PrinterConfig, get_printer
from src.utils.env_reader import EnvReaderUtil

class FormatUtil:
    _ASSET_DIR = Path("assets")

    @classmethod
    def _prepare_img(
        cls,
        source: Path,
        destination: Path,
        target_width: int,
    ) -> Path | None:
        """
        Prepares images for receipts
        """

        if not source.exists():
            print(f"Image not found: {source}")
            return None

        if destination.exists():
            print(f"Using cached image: {destination}")
            return destination

        img = Image.open(source).convert("RGBA")

        # White background for transparency
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        background.paste(img, mask=img.split()[3])

        img = background.convert("RGB")

        # Resize
        height = int(img.height * (target_width / img.width))
        img = img.resize((target_width, height), Image.LANCZOS)

        # Convert to black/white
        img = img.convert("1")

        destination.parent.mkdir(parents=True, exist_ok=True)
        img.save(destination)

        print(f"Prepared image: {destination}")

        return destination

    @staticmethod
    def line(width=EnvReaderUtil.printer_paper_pixel_width, height=2):
        """
        Adds straight horizontal line to receipt
        """

        img = Image.new("1", (width, height), 1)
        draw = ImageDraw.Draw(img)
        draw.line((0, 0, width, 0), fill=0, width=2)
        
        printer = get_printer()
        printer.text("\n")
        printer.image(img)
        printer.text("\n")

    @staticmethod
    def left_right(left_word: str, right_word: str) -> str:
        """
        Put one word to the left and another to the right
        """

        return left_word + right_word.rjust(EnvReaderUtil.printer_paper_character_width - len(left_word)) + "\n"

    @staticmethod
    def current_date_time(fmt: str = "%d.%m.%Y um %H:%M:%S") -> str:
        """
        Current date and time formatted
        """

        return datetime.now().strftime(fmt)

    @staticmethod
    def format_money(value: Decimal) -> str:
        """
        Cents (integer) to readable euro string, e.g. 999 → "9.99€"
        """

        amount = (value / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{amount:.2f}€"

    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """
        Convert ISO timestamp into a readable date format.
        """

        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%d.%m.%Y um %H:%M:%S")
        except (ValueError, TypeError):
            return str(timestamp)

    @classmethod
    def to_go_name_img(cls, text: str) -> Image.Image:
        paper_width = EnvReaderUtil.printer_paper_pixel_width
        target_width = int(paper_width * 0.85)

        font_paths = [
            # Linux / Raspberry Pi
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
            # macOS (development)
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/Library/Fonts/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Impact.ttf"),
        ]
        font_path = next((p for p in font_paths if p.exists()), None)

        # Scale font size down until text fits target width
        dummy = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy)
        font = None
        bbox = (0, 0, 0, 0)

        for font_size in range(160, 9, -10):
            try:
                font = ImageFont.truetype(str(font_path), font_size) if font_path else ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            if text_width <= target_width:
                break

        # bbox = (left, top, right, bottom) relative to anchor (0, 0).
        # Image height must fit bbox[3] (absolute bottom) + padding on both sides.
        # Using (bbox[3] - bbox[1]) would undercount when bbox[1] > 0, cutting off the bottom.
        padding = 20
        text_width = bbox[2] - bbox[0]
        img = Image.new("1", (paper_width, bbox[3] + padding * 2), 1)
        draw = ImageDraw.Draw(img)
        x = max(0, (paper_width - text_width) // 2)
        draw.text((x, padding), text, font=font, fill=0)

        return img

    @classmethod
    def footer_img(cls) -> Path | None:
        """
        Footer image
        """

        return cls._prepare_img(
            source=cls._ASSET_DIR / "footer" / "footer.png",
            destination=cls._ASSET_DIR / "footer" / "footer_resized.png",
            target_width=EnvReaderUtil.printer_paper_pixel_width
        )

    @classmethod
    def checkmark_img(cls) -> Path | None:
        """
        Checkmark image
        """

        return cls._prepare_img(
            source=cls._ASSET_DIR / "checkmark.png",
            destination=cls._ASSET_DIR / "checkmark_resized.png",
            target_width=300
        )

    @classmethod
    def sad_face_img(cls) -> Path | None:
        """
        Sad face image
        """

        return cls._prepare_img(
            source=cls._ASSET_DIR / "sad_face.png",
            destination=cls._ASSET_DIR / "sad_face_resized.png",
            target_width=300
        )