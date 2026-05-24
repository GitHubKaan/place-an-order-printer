from PIL import Image, ImageDraw, ImageFont
from src.utils.config import printer
from pathlib import Path

def print_line(width=1000, height=2):
    img = Image.new("1", (width, height), 1)
    draw = ImageDraw.Draw(img)
    draw.line((0, 0, width, 0), fill=0, width=2)
    printer.image(img)

def prepare_pao_logo() -> Path | None:
    logo_src = Path("assets") / "logo" / "pao_logo_black_v1.png"
    logo_dest = Path("assets") / "logo" / "pao_logo_resized.png"

    if not logo_src.exists():
        print("Logo not found at '%s' - skipping logo.", logo_src)
        return None

    img = Image.open(logo_src).convert("RGBA")

    # Apply white background behind transparent areas
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    background.paste(img, mask=img.split()[3])

    img = background.convert("RGB")

    # Resize while preserving aspect ratio
    logo_width = 200
    height = int(img.height * (logo_width / img.width))
    img = img.resize((logo_width, height), Image.LANCZOS)

    # Convert image to black and white
    img = img.convert("1")

    logo_dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(logo_dest)

    print("Logo prepared: %s", logo_dest)

    return logo_dest

def prepare_pao_logo_small() -> Path | None:
    logo_src = Path("assets") / "logo" / "pao_logo_black_v1.png"
    logo_dest = Path("assets") / "logo" / "pao_logo_resized.png"

    if not logo_src.exists():
        print("Logo not found at '%s' - skipping logo.", logo_src)
        return None

    img = Image.open(logo_src).convert("RGBA")

    # Apply white background behind transparent areas
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    background.paste(img, mask=img.split()[3])

    img = background.convert("RGB")

    # Resize while preserving aspect ratio
    logo_width = 80
    height = int(img.height * (logo_width / img.width))
    img = img.resize((logo_width, height), Image.LANCZOS)

    # Convert image to black and white
    img = img.convert("1")

    logo_dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(logo_dest)

    print("Logo prepared: %s", logo_dest)

    return logo_dest

def prepare_turanics_logo() -> Path | None:
    logo_src = Path("assets") / "turanics_logo.png"
    logo_dest = Path("assets") / "turanics_logo_resized.png"

    if not logo_src.exists():
        print("Logo not found at '%s' - skipping logo.", logo_src)
        return None

    img = Image.open(logo_src).convert("RGBA")

    # Apply white background behind transparent areas
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    background.paste(img, mask=img.split()[3])

    img = background.convert("RGB")

    # Resize while preserving aspect ratio
    logo_width = 80
    height = int(img.height * (logo_width / img.width))
    img = img.resize((logo_width, height), Image.LANCZOS)

    # Convert image to black and white
    img = img.convert("1")

    logo_dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(logo_dest)

    print("Logo prepared: %s", logo_dest)

    return logo_dest

def prepare_text_qr_code() -> Path | None:
    logo_src = Path("assets") / "text_qr.png"
    logo_dest = Path("assets") / "text_qr_resized.png"

    if not logo_src.exists():
        print("Logo not found at '%s' - skipping logo.", logo_src)
        return None

    img = Image.open(logo_src).convert("RGBA")

    # Apply white background behind transparent areas
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    background.paste(img, mask=img.split()[3])

    img = background.convert("RGB")

    # Resize while preserving aspect ratio
    logo_width = 575
    height = int(img.height * (logo_width / img.width))
    img = img.resize((logo_width, height), Image.LANCZOS)

    # Convert image to black and white
    img = img.convert("1")

    logo_dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(logo_dest)

    print("Logo prepared: %s", logo_dest)

    return logo_dest

def prepare_checkmark_symbol() -> Path | None:
    symbol_src = Path("assets") / "checkmark.png"
    symbol_dest = Path("assets") / "checkmark.png"

    if not symbol_src.exists():
        print("Symbol not found at '%s' - skipping logo.", symbol_src)
        return None

    img = Image.open(symbol_src).convert("RGBA")

    # Apply white background behind transparent areas
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    background.paste(img, mask=img.split()[3])

    img = background.convert("RGB")

    # Resize while preserving aspect ratio
    logo_width = 300
    height = int(img.height * (logo_width / img.width))
    img = img.resize((logo_width, height), Image.LANCZOS)

    # Convert image to black and white
    img = img.convert("1")

    symbol_dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(symbol_dest)

    print("Logo prepared: %s", symbol_dest)

    return symbol_dest

def combine_logos(logo1_path, logo2_path, spacing=40):
    img1 = Image.open(logo1_path).convert("RGBA")
    img2 = Image.open(logo2_path).convert("RGBA")

    max_height = max(img1.height, img2.height)
    ratio1 = max_height / img1.height
    ratio2 = max_height / img2.height

    img1 = img1.resize((int(img1.width * ratio1), max_height))
    img2 = img2.resize((int(img2.width * ratio2), max_height))

    new_width = img1.width + spacing + img2.width

    combined = Image.new("RGBA", (new_width, max_height), (255, 255, 255, 0))
    combined.paste(img1, (0, 0))
    combined.paste(img2, (img1.width + spacing, 0))

    return combined
