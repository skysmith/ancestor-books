from __future__ import annotations

from dataclasses import dataclass
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
SPREAD_DIR = (
    ROOT
    / "projects/generated/sieger-rides-through-the-snow/renders/sieger-rides-through-the-snow-images"
)
OUTPUT_DIR = ROOT / "output/pdf/sieger-square-v2"
INTERIOR_PAGES_DIR = OUTPUT_DIR / "interior-pages"
PDF_JPEG_DIR = OUTPUT_DIR / "pdf-jpegs"
INTERIOR_PDF = ROOT / "sieger-interior-8x8-bleed-v3.pdf"
INTERIOR_PREVIEW = OUTPUT_DIR / "interior-contact-sheet.png"

COVER_SOURCE = SPREAD_DIR / "sieger-springer-cover.png"
COVER_PNG = ROOT / "sieger-cover-wrap-8x8-24p-v5.png"
COVER_PDF = ROOT / "sieger-cover-wrap-8x8-24p-v5.pdf"

FONT_REGULAR = "/Library/Fonts/Georgia.ttf"
FONT_BOLD = "/Library/Fonts/Georgia Bold.ttf"
FONT_ITALIC = "/Library/Fonts/Georgia Italic.ttf"

PAGE_W = 2438
PAGE_H = 2475
BLEED_W_IN = 8.125
BLEED_H_IN = 8.25
PDF_W = BLEED_W_IN * 72
PDF_H = BLEED_H_IN * 72

COVER_W = 4892
COVER_H = 2475
BACK_W = 2438
SPINE_W = 16
FRONT_X0 = 2454
FRONT_W = COVER_W - FRONT_X0

SNOW_SPREADS = [1, 2, 3, 4, 5, 6]
LEEK_SPREADS = [8, 9, 10, 11, 12]


@dataclass(frozen=True)
class PageSpec:
    number: int
    text: str
    image: Path | None = None
    kicker: str | None = None
    title: str | None = None
    panel: str = "bottom"
    font_size: int = 92
    line_gap: int = 14


@dataclass(frozen=True)
class PanelLayout:
    x: int
    y: int
    max_width: int
    vertical_anchor: str = "top"


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
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=8)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 2
    return load_font(font_path, min_size)


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


def build_frontmatter_page() -> Image.Image:
    art = Image.open(COVER_SOURCE).convert("RGB")
    page = cover_fill(art, (PAGE_W, PAGE_H))

    overlay = Image.new("RGBA", page.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        (160, 180, PAGE_W - 160, 880),
        radius=72,
        fill=(250, 243, 232, 178),
        outline=(184, 162, 137, 180),
        width=4,
    )
    page = Image.alpha_composite(page.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(page)

    title = "Sieger Rides\nThrough the Snow"
    subtitle = "Two true winter stories from Holland, 1900"
    title_font = load_font(FONT_BOLD, 128)
    subtitle_font = load_font(FONT_REGULAR, 48)
    kicker_font = load_font(FONT_ITALIC, 42)

    kicker = "From Sieger Springer's 1900 journal"
    kbox = draw.textbbox((0, 0), kicker, font=kicker_font)
    draw.text(
        ((PAGE_W - (kbox[2] - kbox[0])) / 2, 250),
        kicker,
        font=kicker_font,
        fill=(109, 83, 58),
    )

    title_box = draw.multiline_textbbox((0, 0), title, font=title_font, spacing=10, align="center")
    draw.multiline_text(
        ((PAGE_W - (title_box[2] - title_box[0])) / 2, 345),
        title,
        font=title_font,
        fill=(251, 246, 239),
        spacing=10,
        align="center",
        stroke_width=3,
        stroke_fill=(92, 70, 48),
    )

    sub_box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    draw.text(
        ((PAGE_W - (sub_box[2] - sub_box[0])) / 2, 735),
        subtitle,
        font=subtitle_font,
        fill=(101, 76, 55),
    )
    return page.convert("RGB")


def build_source_note_page() -> Image.Image:
    base = soft_texture((PAGE_W, PAGE_H), (205, 227, 242))
    panel = Image.new("RGBA", base.size, (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rounded_rectangle(
        (170, 220, PAGE_W - 170, PAGE_H - 230),
        radius=80,
        fill=(250, 247, 242, 212),
        outline=(150, 174, 190, 160),
        width=4,
    )
    page = Image.alpha_composite(base, panel)
    draw = ImageDraw.Draw(page)

    title_font = load_font(FONT_BOLD, 82)
    body_font = load_font(FONT_REGULAR, 46)
    small_font = load_font(FONT_REGULAR, 34)

    title = "Source Note"
    title_box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(
        ((PAGE_W - (title_box[2] - title_box[0])) / 2, 320),
        title,
        font=title_font,
        fill=(68, 82, 101),
    )

    body = (
        "These stories are adapted from February and March 1900 journal entries by "
        "Sieger Springer. The first follows his winter trip to Arnhem after the death "
        "of Brother Lau Keilholz. The second tells of his ride to Leek, where he found "
        "a sick woman in a room open to the cold and helped patch the roof with old sacks."
    )
    wrapped = "\n".join(wrap(body, width=44))
    draw.multiline_text(
        (270, 520),
        wrapped,
        font=body_font,
        fill=(76, 88, 105),
        spacing=16,
    )

    footer = "Arranged by Sky Smith"
    foot_box = draw.textbbox((0, 0), footer, font=small_font)
    draw.text(
        ((PAGE_W - (foot_box[2] - foot_box[0])) / 2, PAGE_H - 330),
        footer,
        font=small_font,
        fill=(97, 112, 126),
    )
    return page.convert("RGB")


def split_pages() -> list[Path]:
    pages: list[Path] = []
    INTERIOR_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INTERIOR_PAGES_DIR.glob("page-*.png")):
        path.unlink()
    for spread_number in SNOW_SPREADS + LEEK_SPREADS:
        spread_path = SPREAD_DIR / f"sieger-spread-{spread_number}.png"
        with Image.open(spread_path) as image:
            image = image.convert("RGB")
            midpoint = image.width // 2
            halves = [
                image.crop((0, 0, midpoint, image.height)),
                image.crop((midpoint, 0, image.width, image.height)),
            ]
            for half in halves:
                page_index = len(pages) + 1
                out = INTERIOR_PAGES_DIR / f"page-{page_index:02d}.png"
                half.save(out, quality=95)
                pages.append(out)
    return pages


def square_art_page(image_path: Path) -> Image.Image:
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        return cover_fill(image, (PAGE_W, PAGE_H))


def panel_layout(panel: str) -> PanelLayout:
    if panel == "top":
        return PanelLayout(120, 110, 1240, "top")
    if panel == "center":
        return PanelLayout(0, PAGE_H // 2, 1180, "center")
    if panel == "left":
        return PanelLayout(105, 220, 980, "top")
    return PanelLayout(120, PAGE_H - 145, 1320, "bottom")


def text_block_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    spacing: int = 0,
) -> tuple[int, int]:
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text_panel(page: Image.Image, spec: PageSpec) -> Image.Image:
    layout = panel_layout(spec.panel)
    padding_x = 44
    padding_y = 34
    available_width = layout.max_width - (padding_x * 2)
    measure = ImageDraw.Draw(Image.new("RGBA", page.size, (0, 0, 0, 0)))

    kicker_font = None
    kicker_size = (0, 0)
    if spec.kicker:
        kicker_font = fit_font(measure, spec.kicker, FONT_ITALIC, available_width, 40, 28)
        kicker_size = text_block_size(measure, spec.kicker, kicker_font)

    title_font = None
    title_size = (0, 0)
    if spec.title:
        title_font = fit_font(measure, spec.title, FONT_BOLD, available_width, 74, 52)
        title_size = text_block_size(measure, spec.title, title_font, spacing=8)

    body_start_size = max(44, spec.font_size - 6)
    body_min_size = max(36, body_start_size - 18)
    body_font = fit_font(measure, spec.text, FONT_REGULAR, available_width, body_start_size, body_min_size)
    body_size = text_block_size(measure, spec.text, body_font, spacing=spec.line_gap)

    content_width = max(kicker_size[0], title_size[0], body_size[0])
    content_height = body_size[1]
    if spec.kicker:
        content_height += kicker_size[1] + 18
    if spec.title:
        content_height += title_size[1] + 24

    box_w = min(layout.max_width, content_width + (padding_x * 2))
    box_h = content_height + (padding_y * 2)
    if spec.panel == "center":
        x0 = (PAGE_W - box_w) // 2
    else:
        x0 = min(layout.x, PAGE_W - box_w - 110)
    if layout.vertical_anchor == "center":
        y0 = (PAGE_H - box_h) // 2
    elif layout.vertical_anchor == "bottom":
        y0 = layout.y - box_h
    else:
        y0 = layout.y
    x1 = x0 + box_w
    y1 = y0 + box_h

    overlay = Image.new("RGBA", page.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=42,
        fill=(248, 243, 236, 178),
        outline=(171, 147, 123, 135),
        width=3,
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(1))
    base = Image.alpha_composite(page.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(base)

    inner_left = x0 + padding_x
    top = y0 + padding_y

    if spec.kicker:
        assert kicker_font is not None
        draw.text((inner_left, top), spec.kicker, font=kicker_font, fill=(122, 92, 67))
        kbox = draw.textbbox((inner_left, top), spec.kicker, font=kicker_font)
        top = kbox[3] + 18

    if spec.title:
        assert title_font is not None
        draw.multiline_text(
            (inner_left, top),
            spec.title,
            font=title_font,
            fill=(90, 67, 46),
            spacing=8,
        )
        tbox = draw.multiline_textbbox((inner_left, top), spec.title, font=title_font, spacing=8)
        top = tbox[3] + 24

    draw.multiline_text(
        (inner_left, top),
        spec.text,
        font=body_font,
        fill=(70, 54, 39),
        spacing=spec.line_gap,
    )
    return base.convert("RGB")


def page_specs(art_pages: list[Path]) -> list[PageSpec]:
    return [
        PageSpec(
            number=1,
            title="Sieger Rides\nThrough the Snow",
            text="Two true winter stories from Holland, 1900",
            kicker="From Sieger Springer's journal",
            panel="top",
            font_size=48,
        ),
        PageSpec(
            number=2,
            title="Source Note",
            text=(
                "Retold from Sieger Springer's journal entries for 3 February and 2-11 March 1900.\n\n"
                "Story one follows his trip to Arnhem after the death of Brother Lau Keilholz.\n\n"
                "Story two follows his ride to Leek, where he found a sick woman in a cold bed and helped cover the roof with old sacks."
            ),
            panel="center",
            font_size=54,
        ),
        PageSpec(
            3,
            "In the winter of 1900,\nword came from Arnhem.\n\nBrother Lau Keilholz had died.\n\nSieger was asked to go help.",
            art_pages[0],
            kicker="First journey",
            panel="left",
            font_size=68,
        ),
        PageSpec(
            4,
            "He rode first by bicycle\nfrom Groningen to Meppel.\n\nFrom Meppel\nhe took the train to Zwolle.",
            art_pages[1],
            panel="bottom",
            font_size=70,
        ),
        PageSpec(
            5,
            "The wind was against him.\n\nBy the time he reached Zwolle,\nhe was very tired.",
            art_pages[2],
            panel="top",
            font_size=66,
        ),
        PageSpec(
            6,
            "In Zwolle he did not know\nany names.\n\nSo he kept asking questions.",
            art_pages[3],
            panel="bottom",
            font_size=64,
        ),
        PageSpec(
            7,
            "By asking more and more people,\nhe found Brother and Sister Tassche.\n\nHe slept there that Saturday night.",
            art_pages[4],
            panel="top",
            font_size=62,
        ),
        PageSpec(
            8,
            "On Sunday the weather was bad.\nIt snowed.\n\nHe could not go on by bicycle.",
            art_pages[5],
            panel="bottom",
            font_size=62,
        ),
        PageSpec(
            9,
            "So he took the train to Arnhem.\n\nOn the train he met\nBrother van Dam.",
            art_pages[6],
            panel="bottom",
            font_size=64,
        ),
        PageSpec(
            10,
            "In Arnhem everything was all right.\n\nThey were still able\nto hold a meeting.",
            art_pages[7],
            panel="bottom",
            font_size=68,
        ),
        PageSpec(
            11,
            "The Saints treated him kindly.\n\nBrother Lau was not buried there.",
            art_pages[8],
            panel="center",
            font_size=60,
        ),
        PageSpec(
            12,
            "Sieger helped dress the body\nand later place it in the casket.\n\nIt was the first time in his life\nhe had done that.",
            art_pages[9],
            panel="top",
            font_size=68,
        ),
        PageSpec(
            13,
            "He also visited Brother Emont\nin the hospital.\n\nAfter some days,\nhe started home.",
            art_pages[10],
            panel="top",
            font_size=64,
        ),
        PageSpec(
            14,
            "He went back to Zwolle by train,\npicked up his bicycle,\nand rode into the wind again\nuntil he reached Assen.\n\nFrom there he went to Groningen.",
            art_pages[11],
            panel="bottom",
            font_size=58,
        ),
        PageSpec(
            15,
            "On Friday, March 2,\nSieger rode by bicycle\nto Leek.\n\nA family there wanted\nto hear about the gospel.",
            art_pages[12],
            kicker="Second journey",
            panel="top",
            font_size=62,
        ),
        PageSpec(
            16,
            "The ride from Groningen\ntook about three and a half hours.",
            art_pages[13],
            panel="bottom",
            font_size=76,
        ),
        PageSpec(
            17,
            "In the house was Sister Drent's mother.\n\nShe was about eighty-nine years old\nand very sick in bed.",
            art_pages[14],
            panel="bottom",
            font_size=62,
        ),
        PageSpec(
            18,
            "The bed where she lay\nwas badly exposed to the cold.",
            art_pages[15],
            panel="bottom",
            font_size=64,
        ),
        PageSpec(
            19,
            "So they went outside\nto do something about it.",
            art_pages[16],
            panel="bottom",
            font_size=68,
        ),
        PageSpec(
            20,
            "They put something on the roof\nfor protection.",
            art_pages[17],
            panel="bottom",
            font_size=60,
        ),
        PageSpec(
            21,
            "They used old sacks.\n\nIt was plain work,\nbut it helped.",
            art_pages[18],
            panel="top",
            font_size=64,
        ),
        PageSpec(
            22,
            "The bed was less exposed\nto the cold than before.",
            art_pages[19],
            panel="bottom",
            font_size=66,
        ),
        PageSpec(
            23,
            "Later Sieger wrote to Leek\nand arranged a meeting\nat Widow Drent's house.",
            art_pages[20],
            panel="bottom",
            font_size=62,
        ),
        PageSpec(
            24,
            "On Sunday, March 11,\nhe and Brother van der Werff\nrode there again,\nheld the meeting,\nand came home that evening.",
            art_pages[21],
            panel="top",
            font_size=64,
        ),
    ]


def build_interior_pages() -> list[Path]:
    art_pages = split_pages()
    specs = page_specs(art_pages)
    rendered_paths: list[Path] = []

    for spec in specs:
        if spec.number == 1:
            image = build_frontmatter_page()
        elif spec.number == 2:
            image = build_source_note_page()
        else:
            image = square_art_page(spec.image)  # type: ignore[arg-type]
            image = draw_text_panel(image, spec)

        out_path = OUTPUT_DIR / f"interior-page-{spec.number:02d}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(out_path, quality=95)
        rendered_paths.append(out_path)
    return rendered_paths


def build_pdf(page_paths: list[Path], output_pdf: Path) -> None:
    PDF_JPEG_DIR.mkdir(parents=True, exist_ok=True)
    c = pdf_canvas.Canvas(str(output_pdf), pagesize=(PDF_W, PDF_H))
    for page_path in page_paths:
        jpeg_path = PDF_JPEG_DIR / f"{page_path.stem}.jpg"
        with Image.open(page_path) as image:
            image = image.convert("RGB")
            image.save(jpeg_path, format="JPEG", quality=88, optimize=True, progressive=True)
        c.drawImage(str(jpeg_path), 0, 0, width=PDF_W, height=PDF_H)
        c.showPage()
    c.save()


def build_contact_sheet(page_paths: list[Path], output_path: Path) -> None:
    thumbs: list[Image.Image] = []
    for page_path in page_paths:
        image = Image.open(page_path).convert("RGB")
        image.thumbnail((210, 210))
        thumbs.append(image)

    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * 220 + 20, rows * 220 + 20), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for idx, image in enumerate(thumbs):
        x = 10 + (idx % cols) * 220
        y = 10 + (idx // cols) * 220
        canvas.paste(image, (x, y))
        draw.text((x + 6, y + 194), f"{idx + 1}", fill="black", font=font)
    canvas.save(output_path, quality=95)


def build_cover() -> None:
    front_image = Image.open(COVER_SOURCE).convert("RGBA")
    base = Image.new("RGBA", (COVER_W, COVER_H), (208, 228, 242, 255))
    base = Image.alpha_composite(base, soft_texture((COVER_W, COVER_H), (208, 228, 242)))

    # Baby-blue back cover and spine.
    back_panel = Image.new("RGBA", (BACK_W, COVER_H), (198, 223, 241, 255))
    back_panel = Image.alpha_composite(back_panel, soft_texture((BACK_W, COVER_H), (198, 223, 241)))
    base.paste(back_panel, (0, 0))

    spine = Image.new("RGBA", (SPINE_W, COVER_H), (174, 201, 222, 255))
    base.paste(spine, (BACK_W, 0))

    front_fill = cover_fill(front_image, (FRONT_W, COVER_H))
    base.paste(front_fill, (FRONT_X0, 0))

    fx = Image.new("RGBA", (COVER_W, COVER_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(fx)
    draw.rounded_rectangle(
        (260, 250, BACK_W - 250, 1120),
        radius=72,
        fill=(250, 247, 241, 208),
        outline=(149, 170, 188, 165),
        width=4,
    )
    draw.rounded_rectangle(
        (FRONT_X0 + 140, 110, COVER_W - 130, 760),
        radius=90,
        fill=(34, 20, 10, 56),
    )
    draw.rounded_rectangle(
        (FRONT_X0 + 120, 1830, COVER_W - 120, COVER_H - 110),
        radius=56,
        fill=(42, 25, 12, 90),
    )
    fx = fx.filter(ImageFilter.GaussianBlur(26))
    cover = Image.alpha_composite(base, fx)
    draw = ImageDraw.Draw(cover)

    title_font = load_font(FONT_BOLD, 104)
    sub_font = load_font(FONT_REGULAR, 50)
    author_font = load_font(FONT_REGULAR, 36)
    back_kicker_font = load_font(FONT_BOLD, 76)
    back_body_font = load_font(FONT_REGULAR, 46)

    title = "Sieger Rides\nThrough the Snow"
    title_box = draw.multiline_textbbox((0, 0), title, font=title_font, spacing=8, align="center")
    title_x = FRONT_X0 + (FRONT_W - (title_box[2] - title_box[0])) / 2
    draw.multiline_text(
        (title_x, 185),
        title,
        font=title_font,
        fill=(252, 246, 236),
        spacing=8,
        align="center",
        stroke_width=3,
        stroke_fill=(85, 61, 40),
    )

    subtitle = "Two true winter stories from Holland, 1900"
    sub_box = draw.textbbox((0, 0), subtitle, font=sub_font)
    draw.text(
        (FRONT_X0 + (FRONT_W - (sub_box[2] - sub_box[0])) / 2, COVER_H - 245),
        subtitle,
        font=sub_font,
        fill=(247, 234, 217),
    )

    author = "Arranged by Sky Smith"
    auth_box = draw.textbbox((0, 0), author, font=author_font)
    draw.text(
        (FRONT_X0 + (FRONT_W - (auth_box[2] - auth_box[0])) / 2, COVER_H - 135),
        author,
        font=author_font,
        fill=(247, 240, 229),
    )

    back_kicker = "Two true journal stories from 1900."
    draw.text((320, 340), back_kicker, font=back_kicker_font, fill=(72, 95, 118))

    blurb = (
        "Retold from Sieger Springer's journal for February and March 1900. "
        "In the first story, he travels to Arnhem after the death of Brother Lau "
        "Keilholz. In the second, he rides to Leek, finds a sick woman in a cold "
        "bed, and helps cover the roof with old sacks.\n\nThese are simple stories "
        "of travel, service, and practical care."
    )
    wrapped = "\n".join(wrap(blurb, width=54))
    draw.multiline_text(
        (320, 500),
        wrapped,
        font=back_body_font,
        fill=(78, 99, 120),
        spacing=16,
    )

    source = "Retold from Sieger Springer's journal, February-March 1900"
    draw.text((320, 1030), source, font=author_font, fill=(110, 130, 148))

    barcode_box = (BACK_W - 520, COVER_H - 410, BACK_W - 130, COVER_H - 120)
    draw.rounded_rectangle(barcode_box, radius=18, fill=(240, 248, 253), outline=(160, 182, 198), width=3)
    note_font = load_font(FONT_REGULAR, 24)
    note = "KDP barcode\nclear area"
    note_box = draw.multiline_textbbox((0, 0), note, font=note_font, spacing=6, align="center")
    draw.multiline_text(
        (
            barcode_box[0] + (barcode_box[2] - barcode_box[0] - (note_box[2] - note_box[0])) / 2,
            barcode_box[1] + 92,
        ),
        note,
        font=note_font,
        fill=(117, 138, 153),
        spacing=6,
        align="center",
    )

    cover_rgb = cover.convert("RGB")
    cover_rgb.save(COVER_PNG, quality=95)
    cover_rgb.save(COVER_PDF, resolution=300.0)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rendered_pages = build_interior_pages()
    build_pdf(rendered_pages, INTERIOR_PDF)
    build_contact_sheet(rendered_pages, INTERIOR_PREVIEW)
    build_cover()
    print(f"Built interior PDF at {INTERIOR_PDF}")
    print(f"Built cover PDF at {COVER_PDF}")


if __name__ == "__main__":
    main()
