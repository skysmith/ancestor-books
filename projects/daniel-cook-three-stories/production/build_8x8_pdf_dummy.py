#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT = Path("/Users/sky/Documents/codex/personal/projects/ancestor-books/projects/daniel-cook-three-stories")
ART = PROJECT / "art/generated/chatgpt-2026-04-21"
OUT = PROJECT / "outputs"

DPI = 300
PAGE_W_IN = 8.125
PAGE_H_IN = 8.25
PAGE_W = round(PAGE_W_IN * DPI)
PAGE_H = round(PAGE_H_IN * DPI)

BODY_COLOR = (28, 31, 38)
PANEL_FILL = (247, 239, 222, 128)
PAGE_BG = (242, 235, 220)
SHADOW = (0, 0, 0, 28)


def font_path(*names: str) -> str | None:
    candidates = [
        Path("/System/Library/Fonts/Supplemental"),
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
    ]
    for base in candidates:
        for name in names:
            path = base / name
            if path.exists():
                return str(path)
    return None


SERIF = font_path("Georgia.ttf", "Times New Roman.ttf")
SERIF_BOLD = font_path("Georgia Bold.ttf", "Times New Roman Bold.ttf")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = SERIF_BOLD if bold else SERIF
    if path:
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default(size=size)


PAGES = [
    {
        "page": 1,
        "image": "dc-01-title-page.png",
        "bias": 0.5,
        "text": "",
    },
    {
        "page": 2,
        "image": "dc-02-source-note-hat.png",
        "bias": 0.5,
        "box": "bottom-center",
        "text": "Retold from a family account of Daniel Cook, a soldier in the Revolutionary War.\n\nOnly a few stories were remembered.\n\nBut the stories that remained were not small.",
    },
    {
        "page": 3,
        "image": "dc-03-opening-frame.png",
        "bias": 0.5,
        "box": "top-left",
        "text": "They came from the hard years of the war, when Daniel was a soldier for the States.\n\nWar wore down his body.\n\nBut still, through battles, hunger, fear, and judgment, Daniel Cook was saved.",
    },
    {
        "page": 4,
        "image": "dc-04-dark-scouting-road-brighter.png",
        "bias": 0.25,
        "box": "bottom-center",
        "text": "One dark night, Daniel and one other soldier were sent ahead to scout.",
    },
    {
        "page": 5,
        "image": "dc-04-dark-scouting-road-brighter.png",
        "bias": 0.75,
        "box": "top-center",
        "text": "They went down a hill with a stone wall on each side of the road.\n\nThe night was so dark the road seemed to vanish under their feet.",
    },
    {
        "page": 6,
        "image": "dc-05-enemy-behind-wall.png",
        "bias": 0.25,
        "box": "bottom-center",
        "text": "Then thirty men rose behind the wall.\n\n\"Who comes there?\" a voice called.\n\n\"Friend,\" Daniel answered.",
    },
    {
        "page": 7,
        "image": "dc-05-enemy-behind-wall.png",
        "bias": 0.75,
        "box": "bottom-center",
        "text": "\"Friend to who?\"\n\nDaniel held his ground.\n\n\"Friend to the States.\"\n\nThen the dark figures shouted, \"Surrender!\"",
    },
    {
        "page": 8,
        "image": "dc-06-fired-at-hat-shot-revised.png",
        "bias": 0.25,
        "box": "bottom-left",
        "text": "In that instant, Daniel raised his musket.\n\nHe fired at the largest man and ran for the opposite wall.",
    },
    {
        "page": 9,
        "image": "dc-06-fired-at-hat-shot-revised.png",
        "bias": 0.75,
        "box": "top-left",
        "text": "The bullets came after him like hailstones.\n\nOne tore through his hat.\nOne cut his ear.\nOne grazed his side.\nOne struck the heel of his shoe.\n\nStill Daniel ran.",
    },
    {
        "page": 10,
        "image": "dc-07-i-give-up-relief.png",
        "bias": 0.5,
        "box": "bottom-center",
        "text": "Down the hill he went until more figures appeared in the dark ahead.\n\n\"I give up! I give up!\" he cried.\n\nThen lantern light showed faces he knew.\n\nHis own men.",
    },
    {
        "page": 11,
        "image": "dc-08-morning-after-wall.png",
        "bias": 0.5,
        "box": "bottom-left",
        "text": "In the morning, the men returned to the wall.\n\nThere was blood on the ground. Perhaps Daniel's shot had found its mark.\n\nDaniel looked at the road, the wall, and the hat with the hole in it.\n\nHe had lived. That was enough.",
    },
    {
        "page": 12,
        "image": "page-12-hungry-winter-captain-left-square.png",
        "bias": 0.5,
        "box": "top-right",
        "text": "Another time, hunger drove Daniel's company almost to desperation.\n\nTheir horse beef was gone.\n\nNo meat could be found.",
    },
    {
        "page": 13,
        "image": "page-13-hungry-winter-captain-right-square.png",
        "bias": 0.55,
        "box": "top-right",
        "font_size": 50,
        "text": "At last, some of the men roasted their own shoes and ate them.\n\nEven then, the hunger stayed.\n\nSo the captain gave an order.\n\n\"Go out and take some Tory's chickens,\" he said, \"or anything you can find.\"",
    },
    {
        "page": 14,
        "image": "dc-10-tory-property-bulldog-square.png",
        "bias": 0.45,
        "box": "top-left",
        "text": "Nearby lived a Tory, a man who still sided with the king.\n\nHe had plenty.\n\nBut he would sell none.",
    },
    {
        "page": 15,
        "image": "dc-10-tory-property-bulldog-square.png",
        "bias": 0.6,
        "box": "top-left",
        "text": "He also had a large bulldog that guarded the house.\n\nNo one could come near in the night without waking the dog.\n\nSo the soldiers made a plan.\n\nDaniel was chosen as guard.",
    },
    {
        "page": 16,
        "image": "dc-11-tory-doorway-confrontation-square.png",
        "bias": 0.45,
        "box": "top-center",
        "text": "For a moment, the yard was still.\n\nThen the dog came out in a great fury.\n\nDaniel saw he must defend himself.\n\nHe lifted his musket and fired.",
    },
    {
        "page": 17,
        "image": "dc-11-tory-doorway-confrontation-square.png",
        "bias": 0.6,
        "box": "top-center",
        "text": "The shot brought the old Tory to the door in a rage.\n\nDaniel answered him as steadily as he could.\n\nHe held the man there in the cold as long as he could.",
    },
    {
        "page": 18,
        "image": "dc-12-soldiers-carry-honey-bee-house-square.png",
        "bias": 0.5,
        "box": "top-center",
        "text": "By the time Daniel returned to camp, the other soldiers had done their work.\n\nWhile the Tory argued at the door, they had taken honey from the bee house.",
    },
    {
        "page": 19,
        "image": "dc-13-honey-in-chest-improved-square.png",
        "bias": 0.45,
        "box": "bottom-left",
        "text": "The next morning, the old Tory came to camp looking for his honey.\n\nThe captain listened.\n\n\"I do not think my boys have it,\" he said.\n\n\"But we will search.\"",
    },
    {
        "page": 20,
        "image": "dc-13-honey-in-chest-improved-square.png",
        "bias": 0.6,
        "box": "bottom-left",
        "text": "At last they came to a chest.\n\nThe captain opened it, put his hand into a small cask, and pulled it out covered with honey.\n\nThen he slammed down the lid and wiped his hand.\n\n\"Boys what in thunder do you keep soap here for?\"",
    },
    {
        "page": 21,
        "image": "dc-14-soap-line-toothache-improved-square.png",
        "bias": 0.5,
        "box": "bottom-left",
        "text": "Daniel answered quickly.\n\n\"We have to keep it there or the soldiers will steal it from us.\"\n\nJust then, the Tory noticed a soldier whose tongue was swollen from a bee sting.\n\n\"What ails that man?\"\n\n\"He has the toothache,\" the captain said.\n\nThe old Tory looked once more. Then he went away.",
    },
    {
        "page": 22,
        "image": "dc-15-leaves-for-pork-square.png",
        "bias": 0.5,
        "box": "top-right",
        "font_size": 50,
        "width_frac": 0.55,
        "text": "In those days, before General Lafayette came from France, the men were still nearly starving.\n\nThen Daniel heard news from home: there was pork there.\n\nHe asked to go and get some.\n\nThe captain said he could not spare him.\n\nBut that night, Daniel went anyway.",
    },
    {
        "page": 23,
        "image": "dc-16-return-court-martial-square.png",
        "bias": 0.5,
        "box": "bottom-center",
        "font_size": 50,
        "width_frac": 0.58,
        "text": "For eight or ten days he was gone.\n\nThen Daniel came back with a load of pork on his back.\n\nHe had brought food.\n\nBut he had also left without permission.\n\nDaniel was court-martialed and found guilty.\n\nWhen asked what he had to say, he stood his ground.",
    },
    {
        "page": 24,
        "image": "dc-17-pork-feast-closing-square.png",
        "bias": 0.5,
        "box": "bottom-center",
        "font_size": 50,
        "width_frac": 0.62,
        "text": "The officers consulted.\n\nAt last, Daniel was set free.\n\nHe divided the pork all around, and the hungry soldiers had a feast.\n\nA young soldier ran through bullets, stood in the cold, carried food on his back, and lived for his family to remember.",
    },
]


def cover_crop(image: Image.Image, target_w: int, target_h: int, bias: float = 0.5) -> Image.Image:
    image = image.convert("RGB")
    src_w, src_h = image.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        crop_w = round(src_h * target_ratio)
        max_left = src_w - crop_w
        left = round(max_left * bias)
        box = (left, 0, left + crop_w, src_h)
    else:
        crop_h = round(src_w / target_ratio)
        max_top = src_h - crop_h
        top = round(max_top * 0.48)
        box = (0, top, src_w, top + crop_h)
    return image.crop(box).resize((target_w, target_h), Image.Resampling.LANCZOS)


def wrap_paragraph(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    probe = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(probe)
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def layout_text(text: str, max_width: int, max_height: int, start_size: int = 62) -> tuple[ImageFont.FreeTypeFont, list[str], int, int]:
    for size in range(start_size, 39, -2):
        font = load_font(size)
        line_gap = round(size * 0.34)
        paragraph_gap = round(size * 0.65)
        lines: list[str] = []
        for paragraph in text.split("\n\n"):
            if lines:
                lines.append("")
            lines.extend(wrap_paragraph(paragraph.replace("\n", " "), font, max_width))
        total = 0
        for line in lines:
            total += paragraph_gap if line == "" else size + line_gap
        if total <= max_height:
            return font, lines, size + line_gap, paragraph_gap
    font = load_font(40)
    lines = []
    for paragraph in text.split("\n\n"):
        if lines:
            lines.append("")
        lines.extend(wrap_paragraph(paragraph.replace("\n", " "), font, max_width))
    return font, lines, 54, 26


def draw_text_panel(
    page: Image.Image,
    text: str,
    page_number: int,
    title: bool = False,
    anchor: str = "bottom-center",
    start_size: int = 56,
    width_frac: float = 0.72,
) -> None:
    if not text.strip():
        return

    overlay = Image.new("RGBA", page.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    safe_x = round(0.62 * DPI)
    max_text_w = min(PAGE_W - safe_x * 2, round(PAGE_W * width_frac))

    if title:
        panel_h = round(2.05 * DPI)
        y0 = PAGE_H - panel_h - round(0.22 * DPI)
        draw.rounded_rectangle((safe_x - 30, y0 + 14, PAGE_W - safe_x + 30, PAGE_H - round(0.2 * DPI) + 14), radius=34, fill=SHADOW)
        draw.rounded_rectangle((safe_x - 30, y0, PAGE_W - safe_x + 30, PAGE_H - round(0.2 * DPI)), radius=34, fill=PANEL_FILL)
        title_font = load_font(148, bold=True)
        subtitle_font = load_font(64)
        title_text, subtitle = text.split("\n", 1)
        title_box = draw.textbbox((0, 0), title_text, font=title_font)
        subtitle_box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        draw.text(((PAGE_W - (title_box[2] - title_box[0])) / 2, y0 + 88), title_text, font=title_font, fill=BODY_COLOR)
        draw.text(((PAGE_W - (subtitle_box[2] - subtitle_box[0])) / 2, y0 + 270), subtitle, font=subtitle_font, fill=BODY_COLOR)
        page.alpha_composite(overlay)
        return

    max_text_h = round(2.9 * DPI)
    font, lines, line_height, paragraph_gap = layout_text(text, max_text_w, max_text_h, start_size=start_size)
    text_height = sum(paragraph_gap if line == "" else line_height for line in lines)
    pad_x = round(0.17 * DPI)
    pad_y = round(0.15 * DPI)
    line_widths = [
        draw.textbbox((0, 0), line, font=font)[2]
        for line in lines
        if line
    ]
    panel_w = min(max(line_widths or [max_text_w]) + pad_x * 2, PAGE_W - safe_x * 2)
    panel_h = min(text_height + pad_y * 2, round(3.35 * DPI))
    margin = round(0.42 * DPI)
    horizontal = "center"
    vertical = "bottom"
    if "-" in anchor:
        vertical, horizontal = anchor.split("-", 1)

    if horizontal == "left":
        x0 = margin
    elif horizontal == "right":
        x0 = PAGE_W - margin - panel_w
    else:
        x0 = round((PAGE_W - panel_w) / 2)
    x1 = x0 + panel_w

    if vertical == "top":
        y0 = margin
    elif vertical == "middle":
        y0 = round((PAGE_H - panel_h) / 2)
    else:
        y0 = PAGE_H - round(0.3 * DPI) - panel_h
    y1 = y0 + panel_h

    draw.rectangle((x0, y0 + 10, x1, y1 + 10), fill=SHADOW)
    draw.rectangle((x0, y0, x1, y1), fill=PANEL_FILL)

    y = y0 + pad_y
    text_x = x0 + pad_x
    for line in lines:
        if line == "":
            y += paragraph_gap
            continue
        draw.text((text_x, y), line, font=font, fill=BODY_COLOR)
        y += line_height

    page.alpha_composite(overlay)


def render_page(spec: dict) -> Image.Image:
    image_path = ART / spec["image"]
    if image_path.exists():
        page = cover_crop(Image.open(image_path), PAGE_W, PAGE_H, spec.get("bias", 0.5)).convert("RGBA")
    else:
        page = Image.new("RGBA", (PAGE_W, PAGE_H), PAGE_BG + (255,))
        draw = ImageDraw.Draw(page)
        missing_font = load_font(64, bold=True)
        draw.text((180, 340), f"Missing art: {spec['image']}", font=missing_font, fill=(75, 65, 50))
    draw_text_panel(
        page,
        spec["text"],
        spec["page"],
        spec.get("title", False),
        spec.get("box", "bottom-center"),
        spec.get("font_size", 56),
        spec.get("width_frac", 0.72),
    )
    return page.convert("RGB")


def render_art_only_page(spec: dict) -> Image.Image:
    image_path = ART / spec["image"]
    if image_path.exists():
        return cover_crop(Image.open(image_path), PAGE_W, PAGE_H, spec.get("bias", 0.5)).convert("RGB")

    page = Image.new("RGB", (PAGE_W, PAGE_H), PAGE_BG)
    draw = ImageDraw.Draw(page)
    missing_font = load_font(64, bold=True)
    draw.text((180, 340), f"Missing art: {spec['image']}", font=missing_font, fill=(75, 65, 50))
    return page


def make_contact_sheet(pages: list[Image.Image], output: Path) -> None:
    thumb_w = 260
    thumb_h = round(thumb_w * PAGE_H / PAGE_W)
    cols = 6
    rows = 4
    label_h = 38
    gutter = 22
    sheet = Image.new("RGB", (
        cols * thumb_w + (cols + 1) * gutter,
        rows * (thumb_h + label_h) + (rows + 1) * gutter,
    ), (237, 232, 222))
    draw = ImageDraw.Draw(sheet)
    label_font = load_font(22)
    for idx, page in enumerate(pages):
        col = idx % cols
        row = idx // cols
        x = gutter + col * (thumb_w + gutter)
        y = gutter + row * (thumb_h + label_h + gutter)
        sheet.paste(page.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
        label = f"Page {idx + 1}"
        bbox = draw.textbbox((0, 0), label, font=label_font)
        draw.text((x + (thumb_w - (bbox[2] - bbox[0])) / 2, y + thumb_h + 6), label, font=label_font, fill=(55, 53, 48))
    sheet.save(output, quality=92)


def make_spread_pages(pages: list[Image.Image]) -> list[Image.Image]:
    blank = Image.new("RGB", (PAGE_W, PAGE_H), PAGE_BG)
    spreads: list[Image.Image] = []

    def spread(left: Image.Image, right: Image.Image) -> Image.Image:
        canvas = Image.new("RGB", (PAGE_W * 2, PAGE_H), PAGE_BG)
        canvas.paste(left, (0, 0))
        canvas.paste(right, (PAGE_W, 0))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((PAGE_W - 2, 0, PAGE_W + 1, PAGE_H), fill=(210, 202, 190))
        return canvas

    spreads.append(spread(blank, pages[0]))
    for idx in range(1, len(pages) - 1, 2):
        spreads.append(spread(pages[idx], pages[idx + 1]))
    spreads.append(spread(pages[-1], blank))
    return spreads


def make_spread_contact_sheet(spreads: list[Image.Image], output: Path) -> None:
    thumb_w = 420
    thumb_h = round(thumb_w * PAGE_H / (PAGE_W * 2))
    cols = 3
    rows = (len(spreads) + cols - 1) // cols
    label_h = 34
    gutter = 24
    sheet = Image.new("RGB", (
        cols * thumb_w + (cols + 1) * gutter,
        rows * (thumb_h + label_h) + (rows + 1) * gutter,
    ), (237, 232, 222))
    draw = ImageDraw.Draw(sheet)
    label_font = load_font(21)
    for idx, image in enumerate(spreads):
        col = idx % cols
        row = idx // cols
        x = gutter + col * (thumb_w + gutter)
        y = gutter + row * (thumb_h + label_h + gutter)
        sheet.paste(image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
        if idx == 0:
            label = "blank + 1"
        elif idx == len(spreads) - 1:
            label = "24 + blank"
        else:
            left_page = idx * 2
            label = f"{left_page}-{left_page + 1}"
        bbox = draw.textbbox((0, 0), label, font=label_font)
        draw.text((x + (thumb_w - (bbox[2] - bbox[0])) / 2, y + thumb_h + 6), label, font=label_font, fill=(55, 53, 48))
    sheet.save(output, quality=92)


def write_asset_map(output: Path) -> None:
    lines = [
        "# Daniel Cook 24-Page PDF Dummy Asset Map",
        "",
        f"PDF page size: {PAGE_W_IN} x {PAGE_H_IN} inches at {DPI} DPI.",
        "Trim target: 8 x 8 inches with KDP bleed allowance included.",
        "",
        "| Page | Image | Notes |",
        "| ---: | --- | --- |",
    ]
    for spec in PAGES:
        notes = "title" if spec.get("title") else ""
        lines.append(f"| {spec['page']} | `{spec['image']}` | {notes} |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT / "daniel-cook-24-page-8x8-kdp-bleed-draft-v3.pdf"
    spread_pdf_path = OUT / "daniel-cook-24-page-8x8-spread-view-draft-v3.pdf"
    art_only_pdf_path = OUT / "daniel-cook-24-page-8x8-kdp-bleed-art-only-v1.pdf"
    contact_path = OUT / "daniel-cook-24-page-8x8-kdp-bleed-draft-v3-contact-sheet.jpg"
    spread_contact_path = OUT / "daniel-cook-24-page-8x8-spread-view-draft-v3-contact-sheet.jpg"
    art_only_contact_path = OUT / "daniel-cook-24-page-8x8-kdp-bleed-art-only-v1-contact-sheet.jpg"
    map_path = OUT / "daniel-cook-24-page-8x8-kdp-bleed-draft-v3-asset-map.md"

    pages = [render_page(spec) for spec in PAGES]
    art_only_pages = [render_art_only_page(spec) for spec in PAGES]
    spreads = make_spread_pages(pages)
    pages[0].save(
        pdf_path,
        "PDF",
        resolution=DPI,
        save_all=True,
        append_images=pages[1:],
        quality=95,
    )
    art_only_pages[0].save(
        art_only_pdf_path,
        "PDF",
        resolution=DPI,
        save_all=True,
        append_images=art_only_pages[1:],
        quality=95,
    )
    spreads[0].save(
        spread_pdf_path,
        "PDF",
        resolution=DPI,
        save_all=True,
        append_images=spreads[1:],
        quality=95,
    )
    make_contact_sheet(pages, contact_path)
    make_contact_sheet(art_only_pages, art_only_contact_path)
    make_spread_contact_sheet(spreads, spread_contact_path)
    write_asset_map(map_path)
    print(pdf_path)
    print(spread_pdf_path)
    print(art_only_pdf_path)
    print(contact_path)
    print(spread_contact_path)
    print(art_only_contact_path)
    print(map_path)


if __name__ == "__main__":
    main()
