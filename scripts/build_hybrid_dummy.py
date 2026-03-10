from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CANVAS_W = 1800
CANVAS_H = 1000
ART_H = 560


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
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


TITLE_FONT = load_font(44, bold=True)


def cover_fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((int(src_w * scale), int(src_h * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def build_anchor_sheet(project_root: Path, selects: list[Path], output_prefix: str, book_title: str, outputs_dir: Path) -> Path:
    thumbs: list[Image.Image] = []
    thumb_size = (420, 280)
    for path in selects:
        img = Image.open(path).convert("RGB")
        thumb = cover_fit(img, thumb_size)
        thumbs.append(thumb)

    cols = 2 if len(thumbs) <= 6 else 3
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 460 + 40, rows * 340 + 110), (15, 18, 24))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 24), f"{book_title} - Anchor Selects", font=TITLE_FONT, fill=(245, 239, 229))

    for idx, (thumb, path) in enumerate(zip(thumbs, selects)):
        row = idx // cols
        col = idx % cols
        x = 24 + col * 460
        y = 90 + row * 340
        sheet.paste(thumb, (x, y))
        draw.text((x, y + 292), path.stem, font=load_font(22), fill=(240, 240, 240))

    out_path = outputs_dir / f"{output_prefix}-anchor-selects.png"
    sheet.save(out_path)
    return out_path


def build_pdf(frame_paths: list[Path], out_path: Path) -> None:
    images = [Image.open(path).convert("RGB") for path in frame_paths]
    images[0].save(out_path, save_all=True, append_images=images[1:])
    for img in images:
        img.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("--variant", default="hybrid")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    frames_dir = project_root / "storyboard" / "frames"
    selects_dir = project_root / "storyboard" / "renders" / "selects"
    outputs_dir = project_root / "outputs"
    hybrid_dir = project_root / "storyboard" / f"{args.variant}-frames"
    hybrid_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    output_prefix = project_root.name
    book_title = project_root.name.replace("-", " ").title()

    frame_paths = sorted(frames_dir.glob("*.png"))
    hybrid_paths: list[Path] = []

    for frame_path in frame_paths:
        slug = frame_path.stem
        target_path = hybrid_dir / frame_path.name
        selected_path = selects_dir / f"{slug}-selected.png"
        if not selected_path.exists():
            target_path.write_bytes(frame_path.read_bytes())
            hybrid_paths.append(target_path)
            continue

        base = Image.open(frame_path).convert("RGB")
        art = Image.open(selected_path).convert("RGB")
        art = cover_fit(art, (CANVAS_W, ART_H))
        base.paste(art, (0, 0))
        base.save(target_path, quality=92)
        hybrid_paths.append(target_path)

    selected_images = sorted(selects_dir.glob("*-selected.png"))
    if selected_images:
        build_anchor_sheet(project_root, selected_images, output_prefix, book_title, outputs_dir)

    pdf_name = f"{output_prefix}-{args.variant}-rough-dummy.pdf"
    build_pdf(hybrid_paths, outputs_dir / pdf_name)
    print(f"Built {len(hybrid_paths)} hybrid frames.")


if __name__ == "__main__":
    main()
