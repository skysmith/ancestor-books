from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont


DEFAULT_PROJECT_ROOT = Path(
    "/Users/sky/.openclaw/workspace/ancestor-books/projects/captain-daniel-and-the-night-of-courage"
)

CANVAS_W = 1800
CANVAS_H = 1000


@dataclass
class Unit:
    slug: str
    title: str
    pages: str
    kind: str
    left_text: str = ""
    right_text: str = ""
    full_text: str = ""
    illustration_note: str = ""

    @property
    def story_text(self) -> str:
        if self.kind == "full":
            return self.full_text.strip()
        left = self.left_text.strip()
        right = self.right_text.strip()
        return "\n\n".join(part for part in [left, right] if part)


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
SUBTITLE_FONT = load_font(26, bold=True)
BODY_FONT = load_font(28)
SMALL_FONT = load_font(22)
TINY_FONT = load_font(18)


def parse_dummy_layout(dummy_path: Path) -> tuple[str, list[Unit]]:
    text = dummy_path.read_text()
    title_match = re.search(r"^# (.+)$", text, re.M)
    book_title = title_match.group(1).strip() if title_match else dummy_path.parent.parent.name.replace("-", " ").title()
    units: list[Unit] = [
        Unit(
            slug="page-01-half-title",
            title="Page 1: Half-Title",
            pages="1",
            kind="full",
            full_text=book_title,
            illustration_note="Quiet opening image fragment: hat brim, stone texture, or moonlit road detail.",
        ),
        Unit(
            slug="page-02-copyright",
            title="Page 2: Copyright",
            pages="2",
            kind="full",
            full_text="Copyright / publication page",
            illustration_note="Minimal spot art or open space.",
        ),
        Unit(
            slug="page-03-title-page",
            title="Page 3: Title Page",
            pages="3",
            kind="full",
            full_text=book_title,
            illustration_note="Young Daniel introduced before the conflict fully begins.",
        ),
        Unit(
            slug="page-04-silent-lead-in",
            title="Page 4: Silent Lead-In",
            pages="4",
            kind="full",
            full_text="",
            illustration_note="Empty road between high stone walls before the story begins.",
        ),
    ]

    sections = re.finditer(
        r"### Spread (\d+) \(Pages ([^)]+)\)\n\n(.*?)(?=\n### Spread |\n## Why This Layout Works)",
        text,
        re.S,
    )
    for match in sections:
        num = int(match.group(1))
        pages = match.group(2).strip()
        body = match.group(3).strip()
        slug = f"spread-{num:02d}"
        illustration_note = ""
        note_match = re.search(r"\*\*Illustration note:\*\* (.+)", body)
        if note_match:
            illustration_note = note_match.group(1).strip()
            body = re.sub(r"\n?\*\*Illustration note:\*\* .+", "", body).strip()

        if "**Left Page**" in body:
            left_match = re.search(r"\*\*Left Page\*\*\n\n(.*?)(?=\n\*\*Right Page\*\*)", body, re.S)
            right_match = re.search(r"\*\*Right Page\*\*\n\n(.*)$", body, re.S)
            left_text = clean_md_text(left_match.group(1) if left_match else "")
            right_text = clean_md_text(right_match.group(1) if right_match else "")
            units.append(
                Unit(
                    slug=slug,
                    title=f"Spread {num}",
                    pages=pages,
                    kind="split",
                    left_text=left_text,
                    right_text=right_text,
                    illustration_note=illustration_note,
                )
            )
        else:
            full_match = re.search(r"\*\*Full Spread(?: — Final Page)?\*\*\n\n(.*)$", body, re.S)
            full_text = clean_md_text(full_match.group(1) if full_match else body)
            units.append(
                Unit(
                    slug=slug,
                    title=f"Spread {num}",
                    pages=pages,
                    kind="full",
                    full_text=full_text,
                    illustration_note=illustration_note,
                )
            )
    return book_title, units


def clean_md_text(text: str) -> str:
    text = text.replace("**", "").strip()
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def palette_for_unit(unit: Unit) -> tuple[str, str, str, str]:
    content = f"{unit.story_text} {unit.illustration_note}".lower()
    if "dawn" in content or "morning" in content:
        return ("#5f738b", "#bac7d6", "#d7c59b", "#e8edf2")
    if "firelight" in content or "camp" in content:
        return ("#201717", "#4e2d20", "#d8892e", "#f8d8a5")
    if "flash" in content or "fired" in content or "exploded" in content:
        return ("#181d2e", "#51403d", "#ffb24a", "#fff2cb")
    return ("#1a2232", "#334258", "#9a6a37", "#e2d7b8")


def vertical_gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    w, h = size
    base = Image.new("RGBA", size)
    top_rgb = ImageColor.getrgb(top)
    bottom_rgb = ImageColor.getrgb(bottom)
    for y in range(h):
        ratio = y / max(1, h - 1)
        row = tuple(int(top_rgb[i] * (1 - ratio) + bottom_rgb[i] * ratio) for i in range(3))
        ImageDraw.Draw(base).line((0, y, w, y), fill=row + (255,))
    return base


def draw_mood_art(unit: Unit) -> Image.Image:
    dark, mid, warm, light = palette_for_unit(unit)
    art = vertical_gradient((CANVAS_W, 560), dark, mid)
    draw = ImageDraw.Draw(art, "RGBA")
    content = f"{unit.story_text} {unit.illustration_note}".lower()

    draw.rectangle((0, 460, CANVAS_W, 560), fill=(10, 12, 18, 110))

    if "moon" in content or "night" in content or unit.pages in {"1", "4"}:
        draw.ellipse((160, 70, 280, 190), fill=ImageColor.getrgb(light) + (140,))
        draw.ellipse((185, 65, 300, 175), fill=ImageColor.getrgb(dark) + (170,))

    if "wall" in content or "stone" in content or "road" in content:
        draw.polygon([(0, 560), (0, 150), (240, 130), (300, 560)], fill=(50, 55, 63, 210))
        draw.polygon([(CANVAS_W, 560), (CANVAS_W, 140), (1560, 110), (1500, 560)], fill=(55, 60, 68, 220))
        draw.polygon([(560, 560), (900, 320), (1240, 560)], fill=(100, 86, 65, 65))

    if "shadow" in content or "enemy" in content:
        for idx, x in enumerate(range(420, 1380, 110)):
            h = 90 + (idx % 3) * 25
            draw.rectangle((x, 205 - h, x + 24, 205), fill=(20, 24, 30, 220))
            draw.ellipse((x - 8, 175 - h, x + 32, 212 - h), fill=(18, 22, 28, 220))

    if "flash" in content or "fired" in content or "exploded" in content:
        cx, cy = 900, 260
        for angle in range(0, 360, 18):
            outer = 180 + (angle % 36) * 2
            x1 = cx + math.cos(math.radians(angle)) * 20
            y1 = cy + math.sin(math.radians(angle)) * 20
            x2 = cx + math.cos(math.radians(angle)) * outer
            y2 = cy + math.sin(math.radians(angle)) * outer
            draw.line((x1, y1, x2, y2), fill=ImageColor.getrgb(warm) + (230,), width=6)
        draw.ellipse((790, 150, 1010, 370), fill=ImageColor.getrgb(light) + (180,))

    if "firelight" in content or "camp" in content:
        draw.ellipse((260, 345, 410, 430), fill=ImageColor.getrgb(warm) + (185,))
        draw.ellipse((290, 330, 390, 415), fill=ImageColor.getrgb(light) + (170,))
        for x in (840, 980, 1120):
            draw.ellipse((x, 230, x + 60, 330), fill=(24, 27, 33, 170))

    if "dawn" in content or "morning" in content:
        draw.rectangle((0, 0, CANVAS_W, 220), fill=ImageColor.getrgb(light) + (65,))
        draw.rectangle((0, 220, CANVAS_W, 280), fill=ImageColor.getrgb(warm) + (30,))

    if "hat" in content:
        draw.polygon(
            [(1250, 390), (1380, 330), (1510, 395), (1460, 445), (1300, 450)],
            fill=(40, 26, 16, 220),
        )
        draw.ellipse((1300, 392, 1360, 448), fill=(18, 14, 12, 220))

    if unit.slug in {"spread-06", "spread-07"}:
        draw.rectangle((1220, 120, 1520, 560), fill=(92, 95, 105, 140))
        draw.line((980, 450, 1260, 260), fill=ImageColor.getrgb(warm) + (170,), width=8)
        draw.ellipse((930, 360, 990, 420), fill=(25, 28, 36, 210))
        draw.line((950, 410, 920, 500), fill=(25, 28, 36, 210), width=10)
        draw.line((970, 410, 1040, 500), fill=(25, 28, 36, 210), width=10)
        for sx, sy in [(1380, 340), (1510, 260), (1610, 390)]:
            draw.ellipse((sx - 8, sy - 8, sx + 8, sy + 8), fill=ImageColor.getrgb(warm) + (220,))

    if unit.slug in {"spread-10", "spread-13"}:
        draw.ellipse((1160, 190, 1280, 300), fill=(30, 34, 42, 220))
        draw.line((1220, 280, 1180, 390), fill=(30, 34, 42, 220), width=18)
        draw.line((1220, 320, 1320, 415), fill=(30, 34, 42, 220), width=18)

    overlay = Image.new("RGBA", art.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")
    overlay_draw.rounded_rectangle(
        (60, 36, 520, 120), radius=18, fill=(12, 16, 24, 120), outline=(255, 255, 255, 40)
    )
    overlay_draw.text((88, 58), unit.title, font=SUBTITLE_FONT, fill=(245, 239, 229, 255))
    art.alpha_composite(overlay)
    return art


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    if not text:
        return ""
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word]).strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def draw_text_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], heading: str, text: str) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=24, fill=(18, 21, 28, 226), outline=(245, 230, 210, 50), width=2)
    draw.text((x1 + 28, y1 + 22), heading, font=SUBTITLE_FONT, fill=(240, 230, 210, 255))
    wrapped = wrap_text(draw, text, BODY_FONT, max_width=(x2 - x1 - 56))
    draw.multiline_text((x1 + 28, y1 + 72), wrapped, font=BODY_FONT, fill=(245, 243, 236, 255), spacing=10)


def unit_prompt(unit: Unit) -> str:
    story = " ".join(unit.story_text.split())
    note = unit.illustration_note or "Use the established painterly historical realism and restrained picture-book tone."
    return (
        "Painterly historical realism for a children's Revolutionary War picture book. "
        "Young Daniel Cook, visibly teenage and vulnerable rather than heroic, in blue-gray night tones with warm firelight or musket flashes where appropriate. "
        f"Scene focus: {story} "
        f"Illustration direction: {note} "
        "Text-safe composition, emotionally clear faces, textured brushwork, subtle period costume detail, no graphic violence."
    )


def write_prompt_file(unit: Unit) -> None:
    prompt = unit_prompt(unit)
    continuity = [
        "Daniel remains visibly young across the entire book.",
        "Keep his hat consistent until the bullet hole becomes important later.",
        "Use painterly brushwork and historical realism, not slick digital rendering.",
        "Preserve room for text; avoid placing faces behind main copy blocks.",
    ]
    body = [
        f"# {unit.title}",
        "",
        f"- Pages: `{unit.pages}`",
        f"- Type: `{unit.kind}`",
        "",
        "## Story Text",
        "",
        unit.story_text or "_Silent image / front matter page._",
        "",
        "## Illustration Note",
        "",
        unit.illustration_note or "_No explicit note._",
        "",
        "## First-Pass Prompt",
        "",
        prompt,
        "",
        "## Continuity Reminders",
        "",
    ]
    body.extend(f"- {item}" for item in continuity)
    (PROMPTS_DIR / f"{unit.slug}.md").write_text("\n".join(body).rstrip() + "\n")


def build_frame(unit: Unit) -> Path:
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (10, 12, 18, 255))
    art = draw_mood_art(unit)
    canvas.alpha_composite(art, (0, 0))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.rounded_rectangle((36, 580, 1764, 964), radius=30, fill=(7, 9, 14, 210), outline=(255, 255, 255, 36), width=2)
    draw.text((70, 610), unit.title, font=TITLE_FONT, fill=(247, 241, 232, 255))
    draw.text((70, 664), f"Pages {unit.pages}", font=SMALL_FONT, fill=(214, 193, 162, 255))

    if unit.kind == "split":
        draw_text_panel(draw, (70, 720, 850, 940), "Left Page", unit.left_text or "_")
        draw_text_panel(draw, (915, 720, 1695, 940), "Right Page", unit.right_text or "_")
    else:
        draw_text_panel(draw, (70, 720, 1695, 905), "Full Spread", unit.full_text or "Silent image")

    note_box = (1180, 610, 1695, 704)
    draw.rounded_rectangle(note_box, radius=20, fill=(27, 20, 16, 230), outline=(255, 255, 255, 36), width=2)
    draw.text((1202, 628), "Illustration Note", font=SMALL_FONT, fill=(247, 231, 205, 255))
    note_text = wrap_text(draw, unit.illustration_note or "Use the established Book 1 visual language.", SMALL_FONT, 470)
    draw.multiline_text((1202, 658), note_text, font=TINY_FONT, fill=(242, 237, 228, 255), spacing=6)

    prompt_excerpt = wrap_text(draw, unit_prompt(unit), TINY_FONT, 530)
    draw.rounded_rectangle((70, 912, 1120, 964), radius=14, fill=(23, 28, 34, 230))
    draw.text((86, 925), f"Prompt seed: {prompt_excerpt[:170]}...", font=TINY_FONT, fill=(205, 210, 215, 255))

    canvas.alpha_composite(overlay)
    out_path = FRAMES_DIR / f"{unit.slug}.png"
    canvas.convert("RGB").save(out_path, quality=92)
    return out_path


def build_contact_sheet(frame_paths: list[Path], output_prefix: str, book_title: str, outputs_dir: Path) -> Path:
    thumbs: list[Image.Image] = []
    thumb_size = (420, 233)
    for path in frame_paths:
        img = Image.open(path).convert("RGB")
        img.thumbnail(thumb_size)
        thumb = Image.new("RGB", thumb_size, (12, 14, 18))
        x = (thumb_size[0] - img.width) // 2
        y = (thumb_size[1] - img.height) // 2
        thumb.paste(img, (x, y))
        thumbs.append(thumb)

    cols = 3
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 460 + 40, rows * 293 + 110), (15, 18, 24))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 24), f"{book_title} - Storyboard Contact Sheet", font=TITLE_FONT, fill=(245, 239, 229))
    for idx, thumb in enumerate(thumbs):
        row = idx // cols
        col = idx % cols
        x = 24 + col * 460
        y = 90 + row * 293
        sheet.paste(thumb, (x, y))
    out_path = outputs_dir / f"{output_prefix}-contact-sheet.png"
    sheet.save(out_path)
    return out_path


def build_pdf(frame_paths: list[Path], output_prefix: str, outputs_dir: Path) -> Path:
    images = [Image.open(path).convert("RGB") for path in frame_paths]
    out_path = outputs_dir / f"{output_prefix}-rough-dummy.pdf"
    images[0].save(out_path, save_all=True, append_images=images[1:])
    for img in images:
        img.close()
    return out_path


def build_readme(units: list[Unit], storyboard_root: Path, book_title: str) -> None:
    body = [
        "# Storyboard",
        "",
        f"This folder contains the first-pass visual production package for {book_title}.",
        "",
        "## Contents",
        "",
        "- `prompts/` one prompt/spec sheet per front matter unit and spread",
        "- `frames/` generated rough storyboard boards for review",
        "",
        "## Units",
        "",
    ]
    body.extend(f"- `{unit.slug}` - {unit.title} (pages {unit.pages})" for unit in units)
    (storyboard_root / "README.md").write_text("\n".join(body).rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=str(DEFAULT_PROJECT_ROOT))
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    dummy_path = project_root / "manuscript" / "dummy-layout.md"
    storyboard_root = project_root / "storyboard"
    prompts_dir = storyboard_root / "prompts"
    frames_dir = storyboard_root / "frames"
    outputs_dir = project_root / "outputs"
    output_prefix = project_root.name

    prompts_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    global PROMPTS_DIR, FRAMES_DIR
    PROMPTS_DIR = prompts_dir
    FRAMES_DIR = frames_dir

    book_title, units = parse_dummy_layout(dummy_path)
    build_readme(units, storyboard_root, book_title)

    frame_paths: list[Path] = []
    for unit in units:
        write_prompt_file(unit)
        frame_paths.append(build_frame(unit))

    build_contact_sheet(frame_paths, output_prefix, book_title, outputs_dir)
    build_pdf(frame_paths, output_prefix, outputs_dir)
    print(f"Generated {len(frame_paths)} storyboard frames.")


if __name__ == "__main__":
    main()
