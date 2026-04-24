from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ORDERED_UNITS = [
    "page-01-half-title",
    "page-02-copyright",
    "page-03-title-page",
    "page-04-silent-lead-in",
    "spread-01",
    "spread-02",
    "spread-03",
    "spread-04",
    "spread-05",
    "spread-06",
    "spread-07",
    "spread-08",
    "spread-09",
    "spread-10",
    "spread-11",
    "spread-12",
    "spread-13",
    "spread-14",
]

THUMB_SIZE = (420, 280)
CARD_W = 452
CARD_H = 338
PADDING = 24
HEADER_H = 82
BG = (15, 18, 24)
FG = (245, 239, 229)
MUTED = (214, 214, 214)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[str] = []
    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
            ]
        )
    candidates.append("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


TITLE_FONT = load_font(40, bold=True)
LABEL_FONT = load_font(22)


def cover_fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((int(src_w * scale), int(src_h * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def build_contact_sheet(book_title: str, label_prefix: str, selects: list[Path], out_path: Path) -> None:
    cols = 3
    rows = math.ceil(len(selects) / cols)
    width = cols * CARD_W + PADDING * 2
    height = rows * CARD_H + HEADER_H + PADDING
    sheet = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((PADDING, 22), f"{book_title} - Selected Art", font=TITLE_FONT, fill=FG)
    draw.text((PADDING, 58), label_prefix, font=LABEL_FONT, fill=MUTED)

    for idx, path in enumerate(selects):
        row = idx // cols
        col = idx % cols
        x = PADDING + col * CARD_W
        y = HEADER_H + row * CARD_H
        with Image.open(path).convert("RGB") as src:
            thumb = cover_fit(src, THUMB_SIZE)
        sheet.paste(thumb, (x, y))
        draw.text((x, y + THUMB_SIZE[1] + 12), path.stem.replace("-selected", ""), font=LABEL_FONT, fill=FG)

    sheet.save(out_path)


def build_pdf(selects: list[Path], out_path: Path) -> None:
    images: list[Image.Image] = []
    try:
        for path in selects:
            images.append(Image.open(path).convert("RGB"))
        images[0].save(out_path, save_all=True, append_images=images[1:])
    finally:
        for image in images:
            image.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--book-title", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    selects_dir = project_root / "storyboard" / "renders" / "selects"
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    selects = [selects_dir / f"{unit}-selected.png" for unit in ORDERED_UNITS]
    missing = [path.name for path in selects if not path.exists()]
    if missing:
        raise SystemExit(f"Missing selected images: {', '.join(missing)}")

    contact_sheet = outputs_dir / f"{args.output_prefix}-selected-contact-sheet.png"
    pdf_path = outputs_dir / f"{args.output_prefix}-selected-dummy.pdf"
    build_contact_sheet(args.book_title, str(project_root), selects, contact_sheet)
    build_pdf(selects, pdf_path)
    print(contact_sheet)
    print(pdf_path)


if __name__ == "__main__":
    main()
