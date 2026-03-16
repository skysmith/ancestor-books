from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def build_canvas(size: int = 1024) -> Image.Image:
    center = size // 2
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        ratio = y / (size - 1)
        r = int(30 + 80 * ratio)
        g = int(40 + 150 * (ratio ** 1.1))
        b = int(120 + 90 * (ratio ** 0.9))
        draw.line((0, y, size, y), fill=(r, g, b, 255))
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rectangle([0, size * 0.25, size, size], fill=255)
    img.putalpha(mask)
    overlay = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for radius, alpha in ((420, 60), (520, 30)):
        overlay_draw.ellipse(
            [center - radius, center - radius, center + radius, center + radius],
            fill=(255, 255, 255, alpha),
        )
    img = Image.alpha_composite(img, overlay)
    book = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    book_draw = ImageDraw.Draw(book)
    book_width = 520
    book_height = 620
    book_x = center - book_width // 2
    book_y = center - book_height // 2
    book_draw.rounded_rectangle(
        [book_x, book_y, book_x + book_width, book_y + book_height],
        radius=60,
        fill=(255, 255, 255, 220),
    )
    book_draw.line(
        [book_x + book_width // 2, book_y + 60, book_x + book_width // 2, book_y + book_height - 60],
        fill=(237, 192, 90, 220),
        width=18,
    )
    img = Image.alpha_composite(img, book)
    font = ImageFont.load_default()
    for candidate in ("/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/SFNSDisplay.ttf"):
        try:
            font = ImageFont.truetype(candidate, 180)
            break
        except OSError:
            continue
    text = "AB"
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        (center - text_w / 2, center - text_h / 2 + 40),
        text,
        font=font,
        fill=(76, 37, 133, 255),
    )
    return img

def main() -> None:
    icon_path = Path(__file__).resolve().parent.parent / "ImageGenDashboard.icns"
    img = build_canvas()
    img.save(icon_path, format="ICNS", sizes=[16, 32, 64, 128, 256, 512, 1024])


if __name__ == "__main__":
    main()
