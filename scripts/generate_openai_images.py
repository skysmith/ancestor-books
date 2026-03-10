from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path

from openai import OpenAI


def load_jobs(spec_path: Path) -> list[dict[str, str]]:
    data = json.loads(spec_path.read_text())
    if not isinstance(data, list):
        raise ValueError("Spec file must be a JSON list of jobs.")
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Job {idx} is not an object.")
        if "slug" not in item or "prompt" not in item:
            raise ValueError(f"Job {idx} must include slug and prompt.")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("spec_path")
    parser.add_argument("--model", default="gpt-image-1")
    parser.add_argument("--size", default="1536x1024")
    parser.add_argument("--selects", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    project_root = Path(args.project_root).resolve()
    spec_path = Path(args.spec_path).resolve()
    raw_dir = project_root / "storyboard" / "renders" / "raw"
    selects_dir = project_root / "storyboard" / "renders" / "selects"
    raw_dir.mkdir(parents=True, exist_ok=True)
    selects_dir.mkdir(parents=True, exist_ok=True)

    jobs = load_jobs(spec_path)
    client = OpenAI(api_key=api_key)

    for job in jobs:
        slug = job["slug"]
        prompt = job["prompt"]
        result = client.images.generate(model=args.model, size=args.size, prompt=prompt)
        image_bytes = base64.b64decode(result.data[0].b64_json)

        png_path = raw_dir / f"{slug}.png"
        json_path = raw_dir / f"{slug}.json"
        png_path.write_bytes(image_bytes)
        json_path.write_text(
            json.dumps(
                {
                    "slug": slug,
                    "model": args.model,
                    "size": args.size,
                    "prompt": prompt,
                    "source_spec": str(spec_path),
                },
                indent=2,
            )
            + "\n"
        )

        if args.selects:
            selects_png = selects_dir / f"{slug.replace('-v001', '-selected')}.png"
            selects_json = selects_dir / f"{slug.replace('-v001', '-selected')}.json"
            selects_png.write_bytes(image_bytes)
            selects_json.write_text(json_path.read_text())

        print(slug)


if __name__ == "__main__":
    main()
