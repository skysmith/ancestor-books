from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def numeric_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    digits = "".join(ch for ch in stem if ch.isdigit())
    return (int(digits) if digits else 0, stem)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split 2:1 spread images into left/right single pages in reading order."
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing spread images.")
    parser.add_argument("output_dir", type=Path, help="Directory for split single-page images.")
    parser.add_argument(
        "--glob",
        default="spread-*.png",
        help="Glob pattern used to find spread files. Default: spread-*.png",
    )
    parser.add_argument(
        "--prefix",
        default="page",
        help="Filename prefix for output pages. Default: page",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    spreads = sorted(input_dir.glob(args.glob), key=numeric_key)
    if not spreads:
        raise SystemExit(f"No spreads found in {input_dir} matching {args.glob}")

    manifest: list[dict[str, str | int]] = []
    page_number = 1

    for spread in spreads:
        with Image.open(spread) as image:
            image = image.convert("RGB")
            width, height = image.size
            midpoint = width // 2
            left = image.crop((0, 0, midpoint, height))
            right = image.crop((midpoint, 0, width, height))

            left_name = f"{args.prefix}-{page_number:02d}.png"
            right_name = f"{args.prefix}-{page_number + 1:02d}.png"
            left.save(output_dir / left_name, quality=95)
            right.save(output_dir / right_name, quality=95)

            manifest.append(
                {
                    "spread": spread.name,
                    "spread_width": width,
                    "spread_height": height,
                    "left_page": page_number,
                    "left_file": left_name,
                    "right_page": page_number + 1,
                    "right_file": right_name,
                }
            )
            page_number += 2

    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Sliced {len(spreads)} spreads into {len(spreads) * 2} pages at {output_dir}")


if __name__ == "__main__":
    main()
