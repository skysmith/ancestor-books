from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont

try:
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as pdf_canvas
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "reportlab is required. Install it with: python3 -m pip install reportlab"
    ) from exc


ROOT = Path("/Users/sky/Documents/codex/personal/projects/ancestor-books")
CANVA_EXPORT_DIR = ROOT / "tmp/canva-exports/extracted"
OUTPUT_DIR = ROOT / "output/pdf/sieger-canva-kdp"
INTERIOR_PAGES_DIR = OUTPUT_DIR / "interior-pages"
INTERIOR_CONTACT = OUTPUT_DIR / "interior-contact-sheet.png"

INTERIOR_PDF = ROOT / "sieger-interior-8x8-bleed-v3.pdf"
COVER_PNG = ROOT / "sieger-cover-wrap-8x8-24p-v5.png"
COVER_PDF = ROOT / "sieger-cover-wrap-8x8-24p-v5.pdf"

FONT_REGULAR = "/Library/Fonts/Georgia.ttf"
FONT_BOLD = "/Library/Fonts/Georgia Bold.ttf"
FONT_ITALIC = "/Library/Fonts/Georgia Italic.ttf"
FONT_SANS = "/Library/Fonts/Arial.ttf"

PAGE_W = 2438
PAGE_H = 2475
BLEED_W_IN = 8.125
BLEED_H_IN = 8.25
PDF_W = BLEED_W_IN * 72
PDF_H = BLEED_H_IN * 72

COVER_W = 4892
COVER_H = 2475
FRONT_X0 = 2454
FRONT_W = COVER_W - FRONT_X0

ENDING_TEXT = (
    "He went back to Zwolle by train,\n"
    "picked up his bicycle\n"
    "and rode into the wind again\n"
    "with faith at his back"
)


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def cover_fill(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    src_w, src_h = image.size
    dst_w, dst_h = size
    src_ratio = src_w / src_h
    dst_ratio = dst_w / dst_h
    if src_ratio > dst_ratio:
        scale = dst_h / src_h
        new_size = (int(src_w * scale), dst_h)
    else:
        scale = dst_w / src_w
        new_size = (dst_w, int(src_h * scale))
    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    left = max(0, (resized.width - dst_w) // 2)
    top = max(0, (resized.height - dst_h) // 2)
    return resized.crop((left, top, left + dst_w, top + dst_h))


def soft_texture(size: tuple[int, int], base: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", size, base + (255,))
    draw = ImageDraw.Draw(image)
    width, height = size
    for y in range(0, height, 120):
        alpha = 18 if (y // 120) % 2 == 0 else 10
        draw.rectangle((0, y, width, y + 120), fill=(255, 255, 255, alpha))
    for i in range(24):
        x0 = int((i * 173) % width)
        y0 = int((i * 211) % height)
        x1 = min(width, x0 + 460)
        y1 = min(height, y0 + 180)
        draw.ellipse((x0, y0, x1, y1), fill=(255, 255, 255, 22))
    return image.filter(ImageFilter.GaussianBlur(36))


def draw_text_panel(
    image: Image.Image,
    *,
    text: str,
    box: tuple[int, int, int, int],
    font_path: str = FONT_REGULAR,
    start_size: int = 62,
    min_size: int = 34,
    text_fill: tuple[int, int, int] = (91, 73, 58),
    panel_fill: tuple[int, int, int, int] = (247, 241, 232, 228),
    panel_outline: tuple[int, int, int, int] = (189, 170, 150, 180),
    radius: int = 34,
    spacing: int = 12,
) -> Image.Image:
    left, top, right, bottom = box
    page = image.convert("RGBA")
    overlay = Image.new("RGBA", page.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if radius > 0:
        draw.rounded_rectangle(box, radius=radius, fill=panel_fill, outline=panel_outline, width=3)
    else:
        draw.rectangle(box, fill=panel_fill, outline=panel_outline, width=3)
    page = Image.alpha_composite(page, overlay)
    draw = ImageDraw.Draw(page)

    font_size = start_size
    lines = text.splitlines()
    while font_size >= min_size:
        font = load_font(font_path, font_size)
        widths = [draw.textbbox((0, 0), line, font=font)[2] for line in lines]
        line_height = draw.textbbox((0, 0), "Ag", font=font)[3]
        total_height = line_height * len(lines) + spacing * (len(lines) - 1)
        if max(widths) <= (right - left - 90) and total_height <= (bottom - top - 90):
            break
        font_size -= 2

    font = load_font(font_path, font_size)
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3]
    total_height = line_height * len(lines) + spacing * (len(lines) - 1)
    y = top + ((bottom - top) - total_height) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = left + ((right - left) - line_width) / 2
        draw.text((x, y), line, font=font, fill=text_fill)
        y += line_height + spacing

    return page.convert("RGB")


def finalize_canva_page(page: Image.Image, source_page_number: int) -> Image.Image:
    if source_page_number == 23:
        return draw_text_panel(
            page,
            text=ENDING_TEXT,
            box=(110, 150, 1210, 760),
            font_path=FONT_SANS,
            start_size=54,
            min_size=34,
            radius=0,
            spacing=14,
        )
    return page


def build_endpaper_page() -> Image.Image:
    # Keep the manuscript at KDP's 24-page minimum without a near-blank opening page.
    page = Image.new("RGB", (PAGE_W, PAGE_H), (214, 231, 244))
    draw = ImageDraw.Draw(page)
    draw.rectangle((0, 0, PAGE_W, 110), fill=(225, 238, 248))
    draw.rectangle((0, PAGE_H - 120, PAGE_W, PAGE_H), fill=(225, 238, 248))
    return page


def prepare_page_sources() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INTERIOR_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for pattern in ("page-*.png", "page-*.jpg"):
        for path in INTERIOR_PAGES_DIR.glob(pattern):
            path.unlink()

    page_paths: list[Path] = []

    for page_number, source_page_number in enumerate(range(2, 25), start=1):
        source = CANVA_EXPORT_DIR / f"{source_page_number}.png"
        if not source.exists():
            raise FileNotFoundError(f"Missing Canva export page: {source}")
        with Image.open(source) as image:
            page = cover_fill(image.convert("RGB"), (PAGE_W, PAGE_H))
        page = finalize_canva_page(page, source_page_number)
        out = INTERIOR_PAGES_DIR / f"page-{page_number:02d}.jpg"
        page.save(out, quality=92, optimize=True, progressive=True)
        page_paths.append(out)

    endpaper_out = INTERIOR_PAGES_DIR / "page-24.jpg"
    build_endpaper_page().save(endpaper_out, quality=92, optimize=True, progressive=True)
    page_paths.append(endpaper_out)

    if len(page_paths) != 24:
        raise ValueError(f"Expected 24 interior pages, found {len(page_paths)}")

    return page_paths


def build_contact_sheet(page_paths: list[Path]) -> None:
    thumbs: list[Image.Image] = []
    for path in page_paths:
        with Image.open(path) as image:
            thumb = image.convert("RGB")
            thumb.thumbnail((220, 220))
        cell = Image.new("RGB", (240, 280), "white")
        x = (240 - thumb.width) // 2
        y = 10 + (220 - thumb.height) // 2
        cell.paste(thumb, (x, y))
        draw = ImageDraw.Draw(cell)
        draw.text((10, 248), path.stem.replace("page-", ""), fill="black")
        thumbs.append(cell)

    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 240, rows * 280), (235, 235, 235))
    for index, thumb in enumerate(thumbs):
        x = (index % cols) * 240
        y = (index // cols) * 280
        sheet.paste(thumb, (x, y))
    sheet.save(INTERIOR_CONTACT)


def build_interior_pdf(page_paths: list[Path]) -> None:
    pdf = pdf_canvas.Canvas(str(INTERIOR_PDF), pagesize=(PDF_W, PDF_H))
    for path in page_paths:
        pdf.drawImage(ImageReader(str(path)), 0, 0, width=PDF_W, height=PDF_H)
        pdf.showPage()
    pdf.save()


def build_cover() -> None:
    if not COVER_PNG.exists():
        raise FileNotFoundError(f"Missing existing cover wrap PNG: {COVER_PNG}")

    front_source = CANVA_EXPORT_DIR / "1.png"
    if not front_source.exists():
        raise FileNotFoundError(f"Missing Canva export cover page: {front_source}")

    with Image.open(COVER_PNG) as base_image:
        cover = base_image.convert("RGB")
    with Image.open(front_source) as front_image:
        front_panel = cover_fill(front_image.convert("RGB"), (FRONT_W, COVER_H))

    cover.paste(front_panel, (FRONT_X0, 0))
    cover.save(COVER_PNG, quality=95)
    cover.save(COVER_PDF, resolution=300.0)


def main() -> None:
    page_paths = prepare_page_sources()
    build_contact_sheet(page_paths)
    build_interior_pdf(page_paths)
    build_cover()
    print(f"Built interior PDF at {INTERIOR_PDF}")
    print(f"Built cover PDF at {COVER_PDF}")
    print(f"Built preview at {INTERIOR_CONTACT}")


if __name__ == "__main__":
    main()
