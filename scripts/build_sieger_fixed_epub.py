from __future__ import annotations

import html
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path("/Users/sky/Documents/codex/personal/projects/ancestor-books")
CANVA_EXPORT_DIR = ROOT / "tmp/canva-exports/extracted"
PRINT_PAGE_DIR = ROOT / "output/pdf/sieger-canva-kdp/interior-pages"
OUTPUT_DIR = ROOT / "output/ebook/sieger-fixed-layout"
BUILD_DIR = OUTPUT_DIR / "build"

EPUB_PATH = OUTPUT_DIR / "sieger-rides-through-the-snow-fixed-layout.epub"
MARKETING_COVER = OUTPUT_DIR / "sieger-rides-through-the-snow-ebook-cover.jpg"
MARKETING_COVER_SQUARE_PRESERVED = (
    OUTPUT_DIR / "sieger-rides-through-the-snow-ebook-cover-square-preserved.jpg"
)
HANDOFF_NOTE = OUTPUT_DIR / "kdp-ebook-upload-note.txt"

TITLE = "Sieger Rides Through the Snow"
AUTHOR = "Skyler Smith"
LANGUAGE = "en"
IDENTIFIER = "urn:uuid:2b704535-e4e3-480c-8814-8e9a64d55b54"

PAGE_W = 2438
PAGE_H = 2475
MARKETING_COVER_W = 1600
MARKETING_COVER_H = 2560

TOC_ENTRIES = [
    ("Cover", "text/cover.xhtml"),
    ("Source Note", "text/page-001.xhtml"),
    ("The Winter Journey", "text/page-004.xhtml"),
    ("The Ride to Leek", "text/page-012.xhtml"),
    ("Homeward", "text/page-022.xhtml"),
]


def reset_build_dir() -> None:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    for subdir in [
        BUILD_DIR / "META-INF",
        BUILD_DIR / "OEBPS/text",
        BUILD_DIR / "OEBPS/images",
        BUILD_DIR / "OEBPS/styles",
    ]:
        subdir.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


def fit_inside(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    dst_w, dst_h = size
    src_w, src_h = image.size
    scale = min(dst_w / src_w, dst_h / src_h)
    new_size = (int(src_w * scale), int(src_h * scale))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def save_jpeg(image: Image.Image, path: Path, *, quality: int = 92) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, "JPEG", quality=quality, optimize=True, progressive=True)


def prepare_images() -> list[tuple[str, str, str]]:
    """Return (page_id, filename, alt_text) entries for the EPUB spine."""
    cover_source = CANVA_EXPORT_DIR / "1.png"
    if not cover_source.exists():
        raise FileNotFoundError(f"Missing Canva cover export: {cover_source}")

    with Image.open(cover_source) as image:
        cover_page = cover_fill(image.convert("RGB"), (PAGE_W, PAGE_H))
    save_jpeg(cover_page, BUILD_DIR / "OEBPS/images/cover.jpg")

    pages: list[tuple[str, str, str]] = [
        (
            "cover",
            "cover.jpg",
            "Cover: Sieger Rides Through the Snow, two true winter stories from Holland, 1900.",
        )
    ]

    # The print-only blue endpaper is page 24. Leave it out so the ebook ends on the bike image.
    for page_number in range(1, 24):
        source = PRINT_PAGE_DIR / f"page-{page_number:02d}.jpg"
        if not source.exists():
            raise FileNotFoundError(f"Missing prepared print page: {source}")
        target_name = f"page-{page_number:03d}.jpg"
        with Image.open(source) as image:
            page = cover_fill(image.convert("RGB"), (PAGE_W, PAGE_H))
        save_jpeg(page, BUILD_DIR / f"OEBPS/images/{target_name}")
        pages.append((f"page-{page_number:03d}", target_name, f"{TITLE}, page {page_number}."))

    return pages


def build_marketing_cover() -> None:
    source = CANVA_EXPORT_DIR / "1.png"
    with Image.open(source) as image:
        cover_image = image.convert("RGB")

    portrait_cover = cover_fill(cover_image, (MARKETING_COVER_W, MARKETING_COVER_H))
    save_jpeg(portrait_cover, MARKETING_COVER, quality=95)

    square_cover = fit_inside(cover_image, (MARKETING_COVER_W, MARKETING_COVER_W))
    preserved = Image.new("RGB", (MARKETING_COVER_W, MARKETING_COVER_H), (214, 231, 244))
    draw = ImageDraw.Draw(preserved)
    draw.rectangle((0, 0, MARKETING_COVER_W, 350), fill=(225, 238, 248))
    draw.rectangle((0, MARKETING_COVER_H - 350, MARKETING_COVER_W, MARKETING_COVER_H), fill=(225, 238, 248))
    y = (MARKETING_COVER_H - square_cover.height) // 2
    preserved.paste(square_cover, ((MARKETING_COVER_W - square_cover.width) // 2, y))
    draw.rectangle(
        (0, y, MARKETING_COVER_W - 1, y + square_cover.height - 1),
        outline=(130, 145, 155),
        width=4,
    )
    save_jpeg(preserved, MARKETING_COVER_SQUARE_PRESERVED, quality=95)


def page_xhtml(title: str, image_name: str, alt_text: str) -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <title>{html.escape(title)}</title>
  <meta name="viewport" content="width={PAGE_W}, height={PAGE_H}" />
  <link rel="stylesheet" type="text/css" href="../styles/fixed.css" />
</head>
<body>
  <div class="page">
    <img src="../images/{html.escape(image_name)}" alt="{html.escape(alt_text)}" />
  </div>
</body>
</html>
'''


def write_static_files(pages: list[tuple[str, str, str]]) -> None:
    (BUILD_DIR / "mimetype").write_text("application/epub+zip", encoding="ascii")
    (BUILD_DIR / "META-INF/container.xml").write_text(
        '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
''',
        encoding="utf-8",
    )
    (BUILD_DIR / "OEBPS/styles/fixed.css").write_text(
        f'''@charset "UTF-8";
@page {{ margin: 0; }}
html, body {{
  margin: 0;
  padding: 0;
  width: {PAGE_W}px;
  height: {PAGE_H}px;
  overflow: hidden;
  background: #ffffff;
}}
.page {{
  position: relative;
  width: {PAGE_W}px;
  height: {PAGE_H}px;
  margin: 0;
  padding: 0;
  overflow: hidden;
}}
.page img {{
  position: absolute;
  display: block;
  width: {PAGE_W}px;
  height: {PAGE_H}px;
  left: 0;
  top: 0;
}}
''',
        encoding="utf-8",
    )

    for index, (page_id, image_name, alt_text) in enumerate(pages):
        filename = "cover.xhtml" if page_id == "cover" else f"{page_id}.xhtml"
        title = "Cover" if page_id == "cover" else f"Page {index}"
        (BUILD_DIR / f"OEBPS/text/{filename}").write_text(
            page_xhtml(title, image_name, alt_text),
            encoding="utf-8",
        )


def build_nav() -> None:
    toc_items = "\n".join(
        f'      <li><a href="{html.escape(href)}">{html.escape(label)}</a></li>'
        for label, href in TOC_ENTRIES
    )
    page_items = "\n".join(
        f'      <li><a href="text/page-{page_number:03d}.xhtml">{page_number}</a></li>'
        for page_number in range(1, 24)
    )
    (BUILD_DIR / "OEBPS/nav.xhtml").write_text(
        f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head>
  <title>{html.escape(TITLE)} Navigation</title>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>{html.escape(TITLE)}</h1>
    <ol>
{toc_items}
    </ol>
  </nav>
  <nav epub:type="landmarks" hidden="hidden">
    <h2>Landmarks</h2>
    <ol>
      <li><a epub:type="cover" href="text/cover.xhtml">Cover</a></li>
      <li><a epub:type="bodymatter" href="text/page-001.xhtml">Start</a></li>
    </ol>
  </nav>
  <nav epub:type="page-list" hidden="hidden">
    <h2>Pages</h2>
    <ol>
{page_items}
    </ol>
  </nav>
</body>
</html>
''',
        encoding="utf-8",
    )


def build_ncx() -> None:
    nav_points = "\n".join(
        f'''    <navPoint id="navPoint-{index}" playOrder="{index}">
      <navLabel><text>{html.escape(label)}</text></navLabel>
      <content src="{html.escape(href)}"/>
    </navPoint>'''
        for index, (label, href) in enumerate(TOC_ENTRIES, start=1)
    )
    (BUILD_DIR / "OEBPS/toc.ncx").write_text(
        f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{IDENTIFIER}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{html.escape(TITLE)}</text></docTitle>
  <docAuthor><text>{html.escape(AUTHOR)}</text></docAuthor>
  <navMap>
{nav_points}
  </navMap>
</ncx>
''',
        encoding="utf-8",
    )


def build_opf(pages: list[tuple[str, str, str]]) -> None:
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="style" href="styles/fixed.css" media-type="text/css"/>',
    ]

    spine_items = []
    for page_id, image_name, _alt_text in pages:
        xhtml_name = "cover.xhtml" if page_id == "cover" else f"{page_id}.xhtml"
        properties = ' properties="cover-image"' if page_id == "cover" else ""
        manifest_items.append(
            f'<item id="{page_id}-image" href="images/{image_name}" media-type="image/jpeg"{properties}/>'
        )
        manifest_items.append(
            f'<item id="{page_id}-xhtml" href="text/{xhtml_name}" media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'<itemref idref="{page_id}-xhtml"/>')

    manifest = "\n    ".join(manifest_items)
    spine = "\n    ".join(spine_items)
    (BUILD_DIR / "OEBPS/package.opf").write_text(
        f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" prefix="dcterms: http://purl.org/dc/terms/ rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{IDENTIFIER}</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <dc:language>{LANGUAGE}</dc:language>
    <dc:publisher>Kindle Direct Publishing</dc:publisher>
    <dc:date>2026-04-21</dc:date>
    <meta property="dcterms:modified">{modified}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">auto</meta>
    <meta property="rendition:spread">none</meta>
    <meta name="fixed-layout" content="true"/>
    <meta name="original-resolution" content="{PAGE_W}x{PAGE_H}"/>
    <meta name="orientation-lock" content="none"/>
    <meta name="primary-writing-mode" content="horizontal-lr"/>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    {manifest}
  </manifest>
  <spine toc="ncx" page-progression-direction="ltr">
    {spine}
  </spine>
</package>
''',
        encoding="utf-8",
    )


def package_epub() -> None:
    if EPUB_PATH.exists():
        EPUB_PATH.unlink()
    with zipfile.ZipFile(EPUB_PATH, "w") as epub:
        epub.write(BUILD_DIR / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(BUILD_DIR.rglob("*")):
            if path.is_dir() or path.name == "mimetype":
                continue
            epub.write(path, path.relative_to(BUILD_DIR), compress_type=zipfile.ZIP_DEFLATED)


def write_handoff_note() -> None:
    HANDOFF_NOTE.write_text(
        f"""KDP Kindle eBook upload files

Manuscript:
{EPUB_PATH}

Marketing cover:
{MARKETING_COVER}

Alternate cover if you want the exact square artwork preserved:
{MARKETING_COVER_SQUARE_PRESERVED}

Recommended KDP settings:
- Upload the EPUB as the Kindle eBook manuscript, not the print PDF.
- Upload the JPG as the Kindle eBook cover image.
- DRM: choose "No" if you want buyers to be able to download/export the book more freely.
- Pricing: KDP will not allow a permanent $0.00 list price; use the lowest allowed list price unless you want KDP Select free promo days.

Notes:
- This is a fixed-layout EPUB so the page art and text placement stay intact.
- The print-only blue endpaper is excluded, so the ebook ends on the bike image.
- The EPUB includes a navigation document and landmarks to avoid the missing table of contents warning.
""",
        encoding="utf-8",
    )


def main() -> None:
    reset_build_dir()
    pages = prepare_images()
    build_marketing_cover()
    write_static_files(pages)
    build_nav()
    build_ncx()
    build_opf(pages)
    package_epub()
    write_handoff_note()
    print(f"Built fixed-layout EPUB: {EPUB_PATH}")
    print(f"Built marketing cover: {MARKETING_COVER}")
    print(f"Built handoff note: {HANDOFF_NOTE}")


if __name__ == "__main__":
    main()
