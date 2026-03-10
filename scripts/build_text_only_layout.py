from __future__ import annotations

import argparse
import re
from pathlib import Path


def clean(text: str) -> str:
    text = text.replace("**", "").strip()
    text = text.replace("  \n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_units(dummy_text: str) -> list[dict[str, str]]:
    units: list[dict[str, str]] = [
        {
            "kind": "page",
            "title": "Page 1",
            "label": "Half-Title",
            "text": "",
        },
        {
            "kind": "page",
            "title": "Page 2",
            "label": "Copyright",
            "text": "",
        },
        {
            "kind": "page",
            "title": "Page 3",
            "label": "Title Page",
            "text": "",
        },
        {
            "kind": "page",
            "title": "Page 4",
            "label": "Silent Opening",
            "text": "",
        },
    ]

    pattern = re.finditer(
        r"### Spread (\d+) \(Pages ([^)]+)\)\n\n(.*?)(?=\n### Spread |\n## Why This Layout Works|\Z)",
        dummy_text,
        re.S,
    )
    for match in pattern:
        num = match.group(1)
        pages = match.group(2).strip()
        body = re.sub(r"\n\*\*Illustration note:\*\* .+", "", match.group(3).strip(), flags=re.S)
        if "**Left Page**" in body:
            left = re.search(r"\*\*Left Page\*\*\n\n(.*?)(?=\n\*\*Right Page\*\*)", body, re.S)
            right = re.search(r"\*\*Right Page\*\*\n\n(.*)$", body, re.S)
            units.append(
                {
                    "kind": "spread",
                    "title": f"Spread {num}",
                    "label": f"Pages {pages}",
                    "left": clean(left.group(1) if left else ""),
                    "right": clean(right.group(1) if right else ""),
                }
            )
        else:
            full = re.search(r"\*\*Full Spread(?: — Final Page)?\*\*\n\n(.*)$", body, re.S)
            units.append(
                {
                    "kind": "spread",
                    "title": f"Spread {num}",
                    "label": f"Pages {pages}",
                    "full": clean(full.group(1) if full else body),
                }
            )
    return units


def build_text_only(dummy_path: Path) -> str:
    text = dummy_path.read_text()
    title_match = re.search(r"^# (.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else dummy_path.parent.parent.name.replace("-", " ").title()

    units = parse_units(text)
    lines = [f"# {title}", "", "## Text-Only Layout", ""]

    for unit in units:
        lines.append(f"### {unit['title']} ({unit['label']})")
        lines.append("")
        if unit["kind"] == "page":
            if unit["label"] == "Half-Title":
                lines.append(title)
            elif unit["label"] == "Copyright":
                lines.append("[Copyright page]")
            elif unit["label"] == "Title Page":
                lines.append(title)
            else:
                lines.append("[Silent opening page]")
        elif "full" in unit:
            lines.append(unit["full"])
        else:
            lines.append("Left:")
            lines.append(unit["left"] or "[Blank]")
            lines.append("")
            lines.append("Right:")
            lines.append(unit["right"] or "[Blank]")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="+")
    args = parser.parse_args()

    for root in args.project_root:
        project_root = Path(root).resolve()
        dummy_path = project_root / "manuscript" / "dummy-layout.md"
        out_path = project_root / "manuscript" / "text-only-layout.md"
        out_path.write_text(build_text_only(dummy_path))
        print(out_path)


if __name__ == "__main__":
    main()
