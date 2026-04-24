from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path("/Users/sky/Documents/codex/personal/projects/ancestor-books")
SOURCE = ROOT / "sieger-cover-wrap-8x8-24p-v1.png"
FRONT_SOURCE = Path("/Users/sky/Downloads/sieger-springer-cover.png")
OUT_PNG = ROOT / "sieger-cover-wrap-8x8-24p-v4.png"
OUT_PDF = ROOT / "sieger-cover-wrap-8x8-24p-v4.pdf"
FONT_REGULAR = "/Library/Fonts/Georgia.ttf"
FONT_BOLD = "/Library/Fonts/Georgia Bold.ttf"


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    max_width: int,
    start_size: int,
    min_size: int,
) -> ImageFont.FreeTypeFont:
    size = start_size
    while size >= min_size:
        font = load_font(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 2
    return load_font(font_path, min_size)


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill,
    box,
    line_gap: int = 16,
):
    x0, y0, x1, y1 = box
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= (x1 - x0):
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    y = y0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_h = bbox[3] - bbox[1]
        if y + line_h > y1:
            break
        draw.text((x0, y), line, font=font, fill=fill)
        y += line_h + line_gap


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


def main():
    image = Image.open(SOURCE).convert("RGBA")
    front_image = Image.open(FRONT_SOURCE).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = image.size

    # Match the actual KDP wrap split: two 2438px cover halves plus a thin spine.
    front_x0 = 2454
    spine_x = 2438
    spine_width = front_x0 - spine_x
    front_width = w - front_x0

    # Repair white export bands that were baked into the original back-wrap art.
    back_art = image.crop((0, 48, spine_x, h - 49)).resize((spine_x, h), Image.Resampling.LANCZOS)
    image.paste(back_art, (0, 0))

    # Clear the thin spine area so no prior artwork ghosts through there.
    spine_strip = Image.new("RGBA", (spine_width, h), (219, 205, 184, 255))
    spine_draw = ImageDraw.Draw(spine_strip)
    spine_draw.rectangle((0, 0, spine_width - 1, h - 1), outline=(190, 170, 146, 255), width=1)
    image.paste(spine_strip, (spine_x, 0))

    # Replace the front cover art with the supplied hero image.
    front_fill = cover_fill(front_image, (front_width, h))
    image.paste(front_fill, (front_x0, 0))

    # Warm and darken the lower front area slightly for type readability.
    front_fx = Image.new("RGBA", image.size, (0, 0, 0, 0))
    fx_draw = ImageDraw.Draw(front_fx)
    fx_draw.rectangle((front_x0, 0, w, h), fill=(90, 62, 34, 24))
    fx_draw.rounded_rectangle(
        (front_x0 + 120, 80, w - 120, 760),
        radius=90,
        fill=(34, 20, 10, 46),
    )
    fx_draw.rounded_rectangle(
        (front_x0 + 120, int(h * 0.73), w - 120, h - 110),
        radius=54,
        fill=(42, 25, 12, 88),
    )
    front_fx = front_fx.filter(ImageFilter.GaussianBlur(22))
    image = Image.alpha_composite(image, front_fx)

    # Back cover readability panel.
    back_panel = (340, 150, spine_x - 140, 620)
    draw.rounded_rectangle(back_panel, radius=48, fill=(247, 239, 227, 176))
    draw.rounded_rectangle(
        (back_panel[0] + 18, back_panel[1] + 18, back_panel[2] - 18, back_panel[3] - 18),
        radius=36,
        outline=(128, 92, 62, 92),
        width=3,
    )

    shadow = (48, 31, 19, 180)
    cream = (251, 239, 220, 255)
    back_text = (78, 56, 38, 255)
    muted = (226, 207, 181, 255)

    # Front cover title.
    title = "Sieger Rides\nThrough the Snow"
    title_font = load_font(FONT_BOLD, 100)
    title_bbox = draw.multiline_textbbox((0, 0), title, font=title_font, spacing=4, align="center")
    title_w = title_bbox[2] - title_bbox[0]
    title_x = front_x0 + ((w - front_x0) - title_w) // 2
    title_y = 155
    for dx, dy in [(4, 4), (3, 3)]:
        draw.multiline_text(
            (title_x + dx, title_y + dy),
            title,
            font=title_font,
            fill=shadow,
            spacing=4,
            align="center",
        )
    draw.multiline_text(
        (title_x, title_y),
        title,
        font=title_font,
        fill=cream,
        spacing=4,
        align="center",
    )

    subtitle = "A True Story from Holland, 1900"
    subtitle_font = fit_font(draw, subtitle, FONT_REGULAR, front_width - 260, 52, 40)
    sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = front_x0 + (front_width - sub_w) // 2
    sub_y = int(h * 0.79)
    draw.text((sub_x + 2, sub_y + 2), subtitle, font=subtitle_font, fill=shadow)
    draw.text((sub_x, sub_y), subtitle, font=subtitle_font, fill=muted)

    author = "Arranged by Skyler Smith with the help of AI"
    author_font = load_font(FONT_REGULAR, 34)
    auth_bbox = draw.textbbox((0, 0), author, font=author_font)
    auth_w = auth_bbox[2] - auth_bbox[0]
    auth_x = w - auth_w - 95
    auth_y = h - 105
    draw.text((auth_x + 2, auth_y + 2), author, font=author_font, fill=shadow)
    draw.text((auth_x, auth_y), author, font=author_font, fill=cream)

    # Back cover copy.
    kicker = "A quiet true story of kindness."
    kicker_font = fit_font(draw, kicker, FONT_BOLD, back_panel[2] - back_panel[0] - 140, 66, 50)
    draw.text((back_panel[0] + 70, back_panel[1] + 56), kicker, font=kicker_font, fill=back_text)

    blurb = (
        "On a bitter winter day in 1900, Sieger Springer rides by bicycle from "
        "Groningen to visit a family in Leek. What begins as a pastoral visit "
        "becomes a small, practical act of mercy that warms more than one cold room."
    )
    blurb_font = load_font(FONT_REGULAR, 43)
    draw_wrapped_text(
        draw,
        blurb,
        blurb_font,
        back_text,
        (back_panel[0] + 70, back_panel[1] + 170, back_panel[2] - 70, back_panel[3] - 55),
        line_gap=14,
    )

    out = Image.alpha_composite(image, overlay).convert("RGB")
    out.save(OUT_PNG, quality=95)
    out.save(OUT_PDF, resolution=300.0)


if __name__ == "__main__":
    main()
