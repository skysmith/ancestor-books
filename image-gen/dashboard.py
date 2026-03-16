#!/usr/bin/env python3
from __future__ import annotations

import cgi
import html
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import traceback
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


MODEL = "x/z-image-turbo:latest"
OLLAMA_BIN = shutil.which("ollama") or "/Applications/Ollama.app/Contents/Resources/ollama"
DEFAULT_STEPS = "9"
DEFAULT_SIZE = "1024x1024"
DEFAULT_REVIEW_MODELS = "llava,qwen2.5vl"
DEFAULT_PROMPT_FIXER_MODEL = "llama3.2:3b"
SIZE_OPTIONS = [
    "768x768",
    "1024x1024",
    "1152x896",
    "896x1152",
    "1280x720",
    "720x1280",
]
STEP_OPTIONS = ["4", "6", "8", "9", "10", "12"]

BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
PROMPTS_DIR = OUTPUTS_DIR / "prompts"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR = OUTPUTS_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR = BASE_DIR.parent
REVIEW_SCRIPT = WORKSPACE_DIR / "scripts" / "generate_local_storyboard_images.py"
DEFAULT_REVIEW_PROJECT = WORKSPACE_DIR / "projects" / "04-the-torys-honey"
DATA_DIR = WORKSPACE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
COCKPIT_DIR = BASE_DIR / "cockpit"
SPREADS_FILE = DATA_DIR / "spreads.json"
ASSETS_FILE = DATA_DIR / "assets.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR = WORKSPACE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
GENERATION_CONFIG_FILE = CONFIG_DIR / "generation.json"

DEFAULT_SPREADS = [
    {
        "spread_id": "spread-01",
        "title": "Snowbound Opening",
        "left_page": 2,
        "right_page": 3,
        "layout_type": "span",
        "status": "draft",
        "excerpt": "A wide valley cradles a sleepy village blanketed in snow.",
        "prompt": "Illustration of a snowy valley at dawn, warm light spilling from cottages.",
        "negative_prompt": "no text, no watermark, clean edges",
        "seed": 482137,
        "assigned_image_id": "asset-20260315-001",
        "assigned_image_preview": "",
        "text_overlay_text": "The snow sighed over the valley like a gentle hush.",
        "text_overlay": {
            "visible": True,
            "x": 6,
            "y": 48,
            "width": 66,
            "alignment": "left",
            "wash_opacity": 0.7,
        },
        "notes": "Try adding warmer porch light for depth.",
        "prompt_status": "draft",
        "last_updated_ts": "2026-03-15T10:15:00Z",
    },
    {
        "spread_id": "spread-02",
        "title": "Woodland Edge",
        "left_page": 4,
        "right_page": 5,
        "layout_type": "left",
        "status": "needs-work",
        "excerpt": "Tall pines lean inward as the hero steps into shadow.",
        "prompt": "Child in cloak entering a twilight forest, huskies watching.",
        "negative_prompt": "no modern elements, no logos",
        "seed": 772801,
        "assigned_image_id": "asset-20260315-002",
        "assigned_image_preview": "",
        "text_overlay_text": "He paused, listening to the wind weave through pines.",
        "text_overlay": {
            "visible": True,
            "x": 8,
            "y": 60,
            "width": 52,
            "alignment": "center",
            "wash_opacity": 0.25,
        },
        "notes": "Need moody rim lighting.",
        "prompt_status": "draft",
        "last_updated_ts": "2026-03-15T09:40:00Z",
    },
    {
        "spread_id": "spread-03",
        "title": "River Crossing",
        "left_page": 6,
        "right_page": 7,
        "layout_type": "span",
        "status": "approved",
        "excerpt": "A lantern glows while a wooden bridge weaves through mist.",
        "prompt": "Two children carrying lanterns across a misty river bridge.",
        "negative_prompt": "no modern clothing, no text overlay baked in",
        "seed": 190322,
        "assigned_image_id": None,
        "assigned_image_preview": "",
        "text_overlay_text": "We followed the ribbon of light to the other bank.",
        "text_overlay": {
            "visible": False,
            "x": 7,
            "y": 58,
            "width": 60,
            "alignment": "right",
            "wash_opacity": 0.4,
        },
        "notes": "Save room for map inset.",
        "prompt_status": "approved",
        "last_updated_ts": "2026-03-14T21:22:00Z",
    },
    {
        "spread_id": "spread-04",
        "title": "Firefly Farewell",
        "left_page": 8,
        "right_page": 9,
        "layout_type": "right",
        "status": "draft",
        "excerpt": "Fireflies trace the nighttime path home.",
        "prompt": "Smooth painterly night showing fireflies guiding travelers home.",
        "negative_prompt": "avoid over-saturated neons",
        "seed": 551124,
        "assigned_image_id": "asset-20260315-003",
        "assigned_image_preview": "",
        "text_overlay_text": "The lanterns hovered like tiny promises.",
        "text_overlay": {
            "visible": True,
            "x": 10,
            "y": 35,
            "width": 70,
            "alignment": "left",
            "wash_opacity": 0.45,
        },
        "notes": "",
        "prompt_status": "draft",
        "last_updated_ts": "2026-03-13T17:00:00Z",
    },
]

DEFAULT_ASSETS = [
    {
        "asset_id": "asset-20260315-001",
        "label": "Snow Valley Morning",
        "source_type": "run",
        "mirror_url": "",
        "spread_ids": ["spread-01"],
    },
    {
        "asset_id": "asset-20260315-002",
        "label": "Woodland Husky Watch",
        "source_type": "upload",
        "mirror_url": "",
        "spread_ids": ["spread-02"],
    },
    {
        "asset_id": "asset-20260315-003",
        "label": "Lantern Night",
        "source_type": "run",
        "mirror_url": "",
        "spread_ids": ["spread-04"],
    },
]

DEFAULT_GENERATION_CONFIG = {
    "judge_model": "llama2-70b",
    "judge_threshold": 0.78,
    "max_recursive_fails": 3,
    "prompt_adjustment_strategy": "suggestive",
    "allow_prompt_updates": True,
}

DATA_LOCK = threading.Lock()

STATE = {
    "running": False,
    "status": "Ready",
    "last_run_dir": "",
    "last_images": [],
    "last_error": "",
    "last_review": None,
    "last_review_path": "",
    "last_adjusted_prompt": "",
}
LOCK = threading.Lock()
REVIEW_MODULE = None


def _read_json(path: Path, default: object) -> object:
    with DATA_LOCK:
        if not path.exists():
            path.write_text(json.dumps(default, indent=2) + "\n", encoding="utf-8")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default


def _write_json(path: Path, payload: object) -> None:
    with DATA_LOCK:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_spreads() -> list[dict[str, object]]:
    return _read_json(SPREADS_FILE, DEFAULT_SPREADS)


def save_spreads(spreads: list[dict[str, object]]) -> list[dict[str, object]]:
    _write_json(SPREADS_FILE, spreads)
    return spreads


def load_assets() -> list[dict[str, object]]:
    return _read_json(ASSETS_FILE, DEFAULT_ASSETS)


def save_assets(assets: list[dict[str, object]]) -> list[dict[str, object]]:
    _write_json(ASSETS_FILE, assets)
    return assets


def load_generation_config() -> dict[str, object]:
    return _read_json(GENERATION_CONFIG_FILE, DEFAULT_GENERATION_CONFIG)


def save_generation_config(config: dict[str, object]) -> dict[str, object]:
    _write_json(GENERATION_CONFIG_FILE, config)
    return config


def get_spread(spread_id: str) -> dict[str, object] | None:
    return next((spread for spread in load_spreads() if spread["spread_id"] == spread_id), None)


def patch_spread(spread_id: str, updates: dict[str, object]) -> dict[str, object]:
    spreads = load_spreads()
    assets = load_assets()
    for idx, spread in enumerate(spreads):
        if spread["spread_id"] != spread_id:
            continue
        merged = {**spread}
        if "text_overlay" in updates and isinstance(updates["text_overlay"], dict):
            merged["text_overlay"] = {**merged.get("text_overlay", {}), **updates["text_overlay"]}
        if "generation_overrides" in updates:
            gen_updates = updates["generation_overrides"]
            if gen_updates is None:
                merged["generation_overrides"] = {}
            elif isinstance(gen_updates, dict):
                merged["generation_overrides"] = {**merged.get("generation_overrides", {}), **gen_updates}
        merged.update(
            {k: v for k, v in updates.items() if k not in {"text_overlay", "generation_overrides"}}
        )
        assigned = merged.get("assigned_image_id")
        if assigned:
            asset = next((item for item in assets if item["asset_id"] == assigned), None)
            if asset:
                merged["assigned_image_preview"] = asset.get("mirror_url", "")
        else:
            merged["assigned_image_preview"] = ""
        spreads[idx] = merged
        save_spreads(spreads)
        return merged
    raise ValueError(f"Spread {spread_id} not found")


def add_asset(asset: dict[str, object]) -> dict[str, object]:
    assets = load_assets()
    assets = [item for item in assets if item["asset_id"] != asset["asset_id"]]
    assets.append(asset)
    save_assets(assets)
    return asset


def assign_asset_to_spread(spread_id: str, asset_id: str) -> tuple[dict[str, object], dict[str, object]]:
    updated_spread = patch_spread(spread_id, {"assigned_image_id": asset_id})
    assets = load_assets()
    for asset in assets:
        spreads = set(asset.get("spread_ids") or [])
        if asset["asset_id"] == asset_id:
            spreads.add(spread_id)
        else:
            spreads.discard(spread_id)
        asset["spread_ids"] = list(spreads)
    save_assets(assets)
    updated_asset = next((item for item in assets if item["asset_id"] == asset_id), {})
    return updated_spread, updated_asset


def register_asset_from_run(
    run_dir: Path,
    metadata: dict[str, object],
    image_entries: list[dict[str, object]],
    assign_to_spread: bool = True,
) -> dict[str, object]:
    spread_id = metadata.get("spread_id")
    if not spread_id or not image_entries:
        return
    image_info = image_entries[0]
    mirror_path = Path(image_info["mirror_path"])
    asset_id = run_dir.name
    asset = {
        "asset_id": asset_id,
        "label": metadata.get("prompt", run_dir.name),
        "source_type": "run",
        "mirror_url": f"/mirrors/{mirror_path.name}",
        "spread_ids": [spread_id],
        "run_path": image_info.get("run_path", ""),
        "judge_score": metadata.get("judge_score"),
        "judge_status": metadata.get("review_status"),
        "review_details": metadata.get("review_details"),
        "metadata_path": str(run_dir / "metadata.json"),
        "recursive_config": metadata.get("recursive_config"),
        "attempt": metadata.get("attempt"),
        "failures": metadata.get("failures"),
        "timestamp": metadata.get("timestamp", ""),
    }
    add_asset(asset)
    if assign_to_spread:
        patch_spread(spread_id, {"assigned_image_id": asset_id})
    return asset


def perform_review(run_dir: Path) -> dict[str, object]:
    module = load_review_module()
    image_path = find_primary_image(run_dir)
    if image_path is None:
        raise RuntimeError(f"No image file found in {run_dir}")
    prompt_text = load_run_prompt(run_dir, "prompt.txt")
    settings = load_run_settings(run_dir)
    project_root = Path(settings.get("review_project", str(DEFAULT_REVIEW_PROJECT))).expanduser()
    review_models = split_review_models(settings.get("review_models", DEFAULT_REVIEW_MODELS))
    installed = module.installed_models()
    verdicts = [
        module.safe_review_image(
            image_path,
            model,
            prompt_text=prompt_text,
            project_root=project_root,
            installed=installed,
        )
        for model in review_models
    ]
    aggregate = module.aggregate_reviews(verdicts)
    module.write_scorecards(
        run_dir / "review",
        aggregate,
        verdicts,
        build_review_metadata(run_dir, prompt_text, settings),
    )
    return aggregate


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def set_state(**kwargs: object) -> None:
    with LOCK:
        STATE.update(kwargs)


def get_state() -> dict[str, object]:
    with LOCK:
        return dict(STATE)


def render_options(options: list[str], selected: str) -> str:
    rendered = []
    for option in options:
        sel = " selected" if option == selected else ""
        rendered.append(f'<option value="{html.escape(option)}"{sel}>{html.escape(option)}</option>')
    return "\n".join(rendered)


def load_review_module():
    global REVIEW_MODULE
    if REVIEW_MODULE is not None:
        return REVIEW_MODULE
    spec = importlib.util.spec_from_file_location("local_review_module", REVIEW_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load review helper from {REVIEW_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["local_review_module"] = module
    spec.loader.exec_module(module)
    REVIEW_MODULE = module
    return module


def split_review_models(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def list_image_files(run_dir: Path) -> list[str]:
    return sorted(
        p.name for p in run_dir.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )


def find_primary_image(run_dir: Path) -> Path | None:
    images = [
        p
        for p in run_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ]
    if not images:
        return None
    return max(images, key=lambda path: path.stat().st_mtime)


def load_run_settings(run_dir: Path) -> dict[str, str]:
    settings_path = run_dir / "settings.json"
    if not settings_path.exists():
        return {}
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    return {str(key): "" if value is None else str(value) for key, value in data.items()}


def load_run_prompt(run_dir: Path, preferred_name: str = "adjusted_prompt.txt") -> str:
    preferred = run_dir / preferred_name
    if preferred.exists():
        return preferred.read_text(encoding="utf-8").strip()
    prompt_path = run_dir / "prompt.txt"
    if not prompt_path.exists():
        raise RuntimeError(f"Missing prompt file in {run_dir}")
    return prompt_path.read_text(encoding="utf-8").strip()


def build_review_metadata(run_dir: Path, prompt_text: str, settings: dict[str, str]) -> dict[str, object]:
    return {
        "slug": run_dir.name,
        "unit_slug": run_dir.name,
        "model": settings.get("model", MODEL),
        "width": settings.get("width", ""),
        "height": settings.get("height", ""),
        "steps": settings.get("steps", ""),
        "seed": settings.get("seed", ""),
        "negative_prompt": settings.get("negative", ""),
        "prompt": prompt_text,
        "prompt_file": str(run_dir / "prompt.txt"),
        "review_project": settings.get("review_project", str(DEFAULT_REVIEW_PROJECT)),
        "review_models": split_review_models(settings.get("review_models", DEFAULT_REVIEW_MODELS)),
        "prompt_fixer_model": settings.get("prompt_fixer_model", DEFAULT_PROMPT_FIXER_MODEL),
        "created_at": datetime.now().isoformat(),
    }


def describe_review(review: dict[str, object] | None) -> str:
    if not review:
        return "No review has been run yet."
    return (
        f"Review: {review.get('review_status', 'unknown')} | "
        f"face_lock={review.get('face_lock', 'n/a')} | "
        f"no_text={review.get('no_text', 'n/a')} | "
        f"style_lock={review.get('style_lock', 'n/a')}"
    )


def action_buttons(run_name: str, disabled: str) -> str:
    return f"""
      <form method="post" action="/review-run">
        <input type="hidden" name="run_name" value="{html.escape(run_name)}">
        <button class="linkbtn" type="submit"{disabled}>Review</button>
      </form>
      <form method="post" action="/adjust-run">
        <input type="hidden" name="run_name" value="{html.escape(run_name)}">
        <button class="linkbtn" type="submit"{disabled}>Adjust Prompt</button>
      </form>
      <form method="post" action="/retry-run">
        <input type="hidden" name="run_name" value="{html.escape(run_name)}">
        <button class="linkbtn" type="submit"{disabled}>Retry Adjusted</button>
      </form>
    """


def render_page(message: str = "") -> str:
    state = get_state()
    last_run_dir = str(state["last_run_dir"])
    last_images = state["last_images"] if isinstance(state["last_images"], list) else []
    status = html.escape(str(state["status"]))
    running = bool(state["running"])
    button_label = "Generating..." if running else "Generate"
    disabled = " disabled" if running else ""
    open_last_href = "/open-last" if last_run_dir else "#"
    open_last_disabled = "" if last_run_dir else ' aria-disabled="true"'
    flash = f'<div class="flash">{message}</div>' if message else ""
    last_review = state["last_review"] if isinstance(state["last_review"], dict) else None
    last_review_path = str(state["last_review_path"])
    last_adjusted_prompt = str(state["last_adjusted_prompt"]).strip()

    images_html = ""
    workflow_actions = ""
    if last_run_dir and last_images:
        items = []
        run_name = Path(last_run_dir).name
        for image_name in last_images:
            href = f"/run-image/{html.escape(run_name)}/{html.escape(image_name)}"
            items.append(f'<li><a href="{href}" target="_blank">{html.escape(image_name)}</a></li>')
        images_html = "<ul>" + "".join(items) + "</ul>"
        workflow_actions = f"""
          <div class="actions" style="margin-top:12px;">
            {action_buttons(run_name, disabled)}
          </div>
        """

    review_html = ""
    if last_run_dir:
        bits = [f'<p class="status">{html.escape(describe_review(last_review))}</p>']
        if last_review and last_review.get("notes"):
            bits.append(f'<div class="meta">{html.escape(str(last_review["notes"]))}</div>')
        if last_review_path:
            review_name = Path(last_review_path).name
            bits.append(f'<div class="meta">Review file: <a href="/run-artifact/{html.escape(Path(last_run_dir).name)}/{html.escape(review_name)}" target="_blank">{html.escape(review_name)}</a></div>')
        if last_adjusted_prompt:
            bits.append(
                "<label for=\"adjusted-prompt\" style=\"margin-top:12px;\">Adjusted prompt</label>"
                f"<textarea id=\"adjusted-prompt\" class=\"small-textarea\" readonly>{html.escape(last_adjusted_prompt)}</textarea>"
            )
        review_html = "".join(bits)

    help_html = f"""
      <p class="status">Use this as a local generate-review-retry loop.</p>
      <div class="meta">1. Enter or paste a prompt and click Generate.</div>
      <div class="meta">2. Review checks the latest image in that run folder with the selected local vision models.</div>
      <div class="meta">3. Adjust Prompt rewrites the saved prompt using the review scorecard.</div>
      <div class="meta">4. Retry Adjusted starts a new run from that adjusted prompt with the same size, steps, seed, and negative prompt.</div>
      <div class="meta">Review project points at the book folder whose Daniel anchor should be used for judging. It does not change where files are saved.</div>
      <div class="meta">One-off runs always save to <code>{html.escape(str(PROMPTS_DIR))}</code>. They do not write into a book folder automatically.</div>
      <div class="meta">If you want to promote an image into a book, copy it into that book's storyboard selects/raw area or use the ancestor-books scripts for book-managed renders.</div>
    """

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Image Gen Dashboard</title>
  <style>
    :root {{
      --bg: #f3f6fb;
      --bg-muted: #e9eef7;
      --panel: #ffffff;
      --panel-muted: #f8fafc;
      --border: #d7dee9;
      --text: #142033;
      --text-muted: #617086;
      --text-soft: #7b8799;
      --accent: #2457d6;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ height: 100%; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", "Noto Sans", sans-serif;
      background:
        linear-gradient(180deg, rgba(36, 87, 214, 0.07), transparent 28%),
        var(--bg);
    }}
    .wrap {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 28px 20px 56px;
    }}
    .eyebrow {{
      margin: 0 0 0.6rem;
      color: var(--accent);
      font-size: 0.74rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.16em;
    }}
    h1 {{
      margin: 0.15rem 0 0.35rem;
      font-size: clamp(2.2rem, 4vw, 3.4rem);
      line-height: 0.94;
      letter-spacing: -0.04em;
      font-weight: 800;
    }}
    .sub {{
      margin: 0 0 18px;
      color: var(--text-muted);
      font-size: 1rem;
      line-height: 1.5;
      max-width: 42rem;
    }}
    .flash {{
      margin: 0 0 16px;
      padding: 12px 14px;
      border-radius: 1rem;
      background: rgba(36, 87, 214, 0.08);
      border: 1px solid var(--border);
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 1.5rem;
      padding: 1.15rem;
      box-shadow: 0 18px 40px rgba(20, 32, 51, 0.06);
    }}
    .panel + .panel {{ margin-top: 16px; }}
    .panel-title {{
      margin: 0 0 10px;
      font-size: 1.15rem;
      line-height: 1.05;
    }}
    textarea, select, input {{
      width: 100%;
      min-height: 2.7rem;
      border-radius: 0.9rem;
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      font: inherit;
      padding: 0.85rem 0.95rem;
    }}
    textarea {{
      resize: vertical;
      min-height: 230px;
      line-height: 1.5;
    }}
    textarea::placeholder, input::placeholder {{ color: var(--text-soft); }}
    .small-textarea {{ min-height: 110px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    label {{
      display: block;
      font-size: 0.82rem;
      font-weight: 700;
      margin-bottom: 8px;
      color: var(--text-muted);
    }}
    .actions {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 16px;
    }}
    .actions form {{ margin: 0; }}
    button, .linkbtn {{
      min-height: 2.65rem;
      border: 1px solid transparent;
      border-radius: 999px;
      padding: 0 1rem;
      font: inherit;
      font-size: 0.92rem;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }}
    button.primary {{
      background: var(--accent);
      color: white;
    }}
    .linkbtn {{
      border-color: var(--border);
      background: var(--panel-muted);
      color: var(--text);
    }}
    button:disabled {{
      opacity: 0.55;
      cursor: wait;
    }}
    .status {{
      font-size: 1rem;
      margin: 0;
      line-height: 1.5;
    }}
    .meta {{
      color: var(--text-muted);
      margin-top: 8px;
      font-size: 14px;
    }}
    ul {{ margin: 8px 0 0 18px; }}
    a {{ color: var(--accent); }}
    @media (max-width: 760px) {{
      .grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 34px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <p class="eyebrow">Local Studio</p>
    <h1>Image Gen Dashboard</h1>
    <p class="sub">Photoreal prompt runner for Ollama, without the Terminal sludge.</p>
    {flash}
    <form method="post" action="/generate">
      <section class="panel">
        <h2 class="panel-title">Prompt</h2>
        <label for="prompt">Describe the image you want</label>
        <textarea id="prompt" name="prompt" placeholder="cinematic portrait of a weathered cowboy in golden-hour desert light, 85mm lens, shallow depth of field, highly realistic skin texture"></textarea>
      </section>
      <section class="panel">
        <h2 class="panel-title">Prompt Settings</h2>
        <div class="grid">
          <div>
            <label for="steps">Passes</label>
            <select id="steps" name="steps">{render_options(STEP_OPTIONS, DEFAULT_STEPS)}</select>
          </div>
          <div>
            <label for="size">Size</label>
            <select id="size" name="size">{render_options(SIZE_OPTIONS, DEFAULT_SIZE)}</select>
          </div>
          <div>
            <label for="seed">Seed (optional)</label>
            <input id="seed" name="seed" placeholder="12345">
          </div>
        </div>
        <div style="margin-top:14px;">
          <label for="negative">Negative prompt (optional)</label>
          <textarea class="small-textarea" id="negative" name="negative" placeholder="blurry, distorted hands, extra limbs, low detail"></textarea>
        </div>
        <div class="grid" style="margin-top:14px;">
          <div>
            <label for="review_project">Review project</label>
            <input id="review_project" name="review_project" value="{html.escape(str(DEFAULT_REVIEW_PROJECT))}">
          </div>
          <div>
            <label for="review_models">Review models</label>
            <input id="review_models" name="review_models" value="{html.escape(DEFAULT_REVIEW_MODELS)}">
          </div>
          <div>
            <label for="prompt_fixer_model">Prompt fixer model</label>
            <input id="prompt_fixer_model" name="prompt_fixer_model" value="{html.escape(DEFAULT_PROMPT_FIXER_MODEL)}">
          </div>
        </div>
        <div class="actions">
          <button class="primary" type="submit"{disabled}>{button_label}</button>
          <a class="linkbtn" href="{open_last_href}"{open_last_disabled}>Open Last Output</a>
          <a class="linkbtn" href="/recent" target="_blank" rel="noopener noreferrer">Recent Generations</a>
        </div>
      </section>
    </form>
    <section class="panel">
      <h2 class="panel-title">Status</h2>
      <p class="status">{status}</p>
      <div class="meta">Model: {html.escape(MODEL)}</div>
      {f'<div class="meta">Last run folder: {html.escape(last_run_dir)}</div>' if last_run_dir else ''}
      {images_html}
      {workflow_actions}
    </section>
    <section class="panel">
      <h2 class="panel-title">Local Review Loop</h2>
      {review_html or '<p class="status">Generate an image, then review it, adjust the prompt, and retry from the adjusted prompt.</p>'}
    </section>
    <section class="panel">
      <h2 class="panel-title">Help</h2>
      {help_html}
    </section>
  </div>
</body>
</html>"""


def render_recent_page() -> str:
    runs = []
    for run_dir in sorted(PROMPTS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        images = sorted(
            p.name for p in run_dir.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
        prompt = ""
        prompt_path = run_dir / "prompt.txt"
        if prompt_path.exists():
            prompt = prompt_path.read_text(encoding="utf-8", errors="replace").strip()
        runs.append((run_dir.name, prompt, images))

    cards = []
    for run_name, prompt, images in runs[:40]:
        preview = html.escape(prompt[:220] + ("..." if len(prompt) > 220 else ""))
        images_html = '<p class="meta">No image file detected.</p>'
        review_link = ""
        adjusted_link = ""
        if (PROMPTS_DIR / run_name / "review.scorecard.md").exists():
            review_link = (
                f'<div class="meta"><a href="/run-artifact/{html.escape(run_name)}/review.scorecard.md" target="_blank">Open review</a></div>'
            )
        if (PROMPTS_DIR / run_name / "adjusted_prompt.txt").exists():
            adjusted_link = (
                f'<div class="meta"><a href="/run-artifact/{html.escape(run_name)}/adjusted_prompt.txt" target="_blank">Open adjusted prompt</a></div>'
            )
        if images:
            items = [
                f'<li><a href="/run-image/{html.escape(run_name)}/{html.escape(name)}" target="_blank">{html.escape(name)}</a></li>'
                for name in images
            ]
            images_html = "<ul>" + "".join(items) + "</ul>"
        cards.append(
            f"""
            <article class="panel">
              <h2 class="panel-title">{html.escape(run_name)}</h2>
              <div class="meta"><a href="/open-run/{html.escape(run_name)}">Open folder in Finder</a></div>
              {review_link}
              {adjusted_link}
              <p class="status">{preview or "No prompt saved."}</p>
              {images_html}
              <div class="actions">
                {action_buttons(run_name, "")}
              </div>
            </article>
            """
        )

    empty = '<p class="status">No generations yet.</p>' if not cards else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Recent Generations</title>
  <style>
    :root {{
      --bg: #f3f6fb;
      --panel: #ffffff;
      --border: #d7dee9;
      --text: #142033;
      --text-muted: #617086;
      --accent: #2457d6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", "Noto Sans", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    .wrap {{
      max-width: 1000px;
      margin: 0 auto;
      padding: 28px 20px 56px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(2rem, 4vw, 3rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }}
    .sub {{
      margin: 0 0 20px;
      color: var(--text-muted);
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 1.25rem;
      padding: 1rem 1.1rem;
      box-shadow: 0 12px 28px rgba(20, 32, 51, 0.05);
    }}
    .panel + .panel {{ margin-top: 14px; }}
    .panel-title {{ margin: 0 0 6px; font-size: 1.05rem; }}
    .status {{ margin: 10px 0 0; line-height: 1.5; white-space: pre-wrap; }}
    .meta {{ color: var(--text-muted); font-size: 0.92rem; }}
    a {{ color: var(--accent); }}
    ul {{ margin: 10px 0 0 18px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Recent Generations</h1>
    <p class="sub">Local runs from <code>{html.escape(str(PROMPTS_DIR))}</code></p>
    {empty}
    {''.join(cards)}
  </div>
</body>
</html>"""


def generate_image(form: dict[str, str]) -> str:
    prompt = form.get("prompt", "").strip()
    steps = form.get("steps", DEFAULT_STEPS).strip() or DEFAULT_STEPS
    size = form.get("size", DEFAULT_SIZE).strip() or DEFAULT_SIZE
    seed = form.get("seed", "").strip()
    negative = form.get("negative", "").strip()
    review_project = form.get("review_project", str(DEFAULT_REVIEW_PROJECT)).strip() or str(DEFAULT_REVIEW_PROJECT)
    review_models_raw = form.get("review_models", DEFAULT_REVIEW_MODELS).strip() or DEFAULT_REVIEW_MODELS
    review_models = split_review_models(review_models_raw)
    prompt_fixer_model = form.get("prompt_fixer_model", DEFAULT_PROMPT_FIXER_MODEL).strip() or DEFAULT_PROMPT_FIXER_MODEL
    spread_id = form.get("spread_id", "").strip()
    judge_model = form.get("judge_model", DEFAULT_GENERATION_CONFIG["judge_model"]).strip()
    judge_threshold = form.get("judge_threshold", str(DEFAULT_GENERATION_CONFIG["judge_threshold"])).strip()
    max_recursive_fails = form.get(
        "max_recursive_fails", str(DEFAULT_GENERATION_CONFIG["max_recursive_fails"])
    ).strip()
    prompt_adjustment_strategy = form.get(
        "prompt_adjustment_strategy", DEFAULT_GENERATION_CONFIG["prompt_adjustment_strategy"]
    ).strip()
    allow_prompt_updates = form.get(
        "allow_prompt_updates", str(DEFAULT_GENERATION_CONFIG["allow_prompt_updates"])
    ).strip()

    if not prompt:
        return "Prompt is required."
    if "x" not in size:
        return "Size is invalid."
    if seed and not seed.lstrip("-").isdigit():
        return "Seed should be a whole number or blank."
    if not review_models:
        return "Review models should be a comma-separated list."
    if get_state()["running"]:
        return "Generation already in progress."

    width, height = size.split("x", 1)
    recursive_config = {
        "judge_model": judge_model,
        "judge_threshold": judge_threshold,
        "max_recursive_fails": max_recursive_fails,
        "prompt_adjustment_strategy": prompt_adjustment_strategy,
        "allow_prompt_updates": allow_prompt_updates.lower() in ("true", "1", "yes"),
    }
    set_state(
        running=True,
        status="Starting generation loop...",
        last_run_dir="",
        last_images=[],
        last_error="",
        last_review=None,
        last_review_path="",
        last_adjusted_prompt="",
    )
    threading.Thread(
        target=run_generation,
        args=(
            prompt,
            width,
            height,
            steps,
            seed,
            negative,
            spread_id,
            recursive_config,
            review_project,
            review_models,
            prompt_fixer_model,
        ),
        daemon=True,
    ).start()
    return "Started generation – see the cockpit log."


def run_generation(
    prompt: str,
    width: str,
    height: str,
    steps: str,
    seed: str,
    negative: str,
    spread_id: str,
    recursive_config: dict[str, object],
    review_project: str,
    review_models: list[str],
    prompt_fixer_model: str,
) -> None:
    max_fails = max(int(recursive_config.get("max_recursive_fails", 0) or 0), 0)
    attempt = 0
    failures = 0
    while True:
        attempt += 1
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = PROMPTS_DIR / f"{timestamp}-attempt-{attempt}"
        run_dir.mkdir(parents=True, exist_ok=True)

        (run_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        (run_dir / "negative_prompt.txt").write_text(negative + "\n", encoding="utf-8")
        settings = {
            "model": MODEL,
            "width": width,
            "height": height,
            "steps": steps,
            "seed": seed,
            "negative": negative,
            "created_at": datetime.now().isoformat(),
            "review_project": review_project,
            "review_models": ",".join(review_models),
            "prompt_fixer_model": prompt_fixer_model,
        }
        (run_dir / "settings.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        metadata_path = run_dir / "metadata.json"
        metadata = {
            "timestamp": timestamp,
            "prompt_file": str(run_dir / "prompt.txt"),
            "negative_prompt_file": str(run_dir / "negative_prompt.txt"),
            "settings": settings,
            "review_project": review_project,
            "review_models": review_models,
            "prompt_fixer_model": prompt_fixer_model,
            "images": [],
            "spread_id": spread_id,
            "prompt": prompt,
            "recursive_config": recursive_config,
            "attempt": attempt,
            "failures": failures,
        }
        set_state(
            running=True,
            status=f"Attempt {attempt}: generating {run_dir.name}",
            last_run_dir=str(run_dir),
            last_images=[],
            last_error="",
            last_review=None,
            last_review_path="",
            last_adjusted_prompt="",
        )
        try:
            cmd = [OLLAMA_BIN, "run", MODEL, prompt, "--width", width, "--height", height, "--steps", steps]
            if negative:
                cmd.extend(["--negative", negative])
            if seed:
                cmd.extend(["--seed", seed])
            proc = subprocess.run(cmd, cwd=run_dir, capture_output=True, text=True, check=False)
            (run_dir / "ollama.stdout.log").write_text(proc.stdout, encoding="utf-8")
            (run_dir / "ollama.stderr.log").write_text(proc.stderr, encoding="utf-8")
            image_files = list_image_files(run_dir)
            image_entries: list[dict[str, object]] = []
            if proc.returncode == 0 and image_files:
                status = f"Saved {image_files[0]} in {run_dir.name}"
                for image_name in image_files:
                    src = run_dir / image_name
                    dest = IMAGES_DIR / f"{run_dir.name}-{image_name}"
                    shutil.copy2(src, dest)
                    image_entries.append(
                        {
                            "name": image_name,
                            "run_path": str(src),
                            "mirror_path": str(dest),
                        }
                    )
                metadata["images"] = image_entries
                metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
                (run_dir / "images.json").write_text(json.dumps(image_entries, indent=2) + "\n", encoding="utf-8")
                try:
                    aggregate = perform_review(run_dir)
                except Exception as exc:
                    (run_dir / "review.error.log").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
                    set_state(
                        running=False,
                        status=f"Review failed: {type(exc).__name__}: {exc}",
                        last_run_dir=str(run_dir),
                        last_images=image_files,
                        last_error=str(exc),
                    )
                    return
                metadata["review_status"] = aggregate.get("review_status")
                metadata["review_details"] = aggregate
                metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
                assign_final = aggregate.get("review_status", "").lower() == "pass" or failures >= max_fails
                register_asset_from_run(run_dir, metadata, image_entries, assign_to_spread=assign_final)
                set_state(
                    running=not assign_final,
                    status="Judge " + aggregate.get("review_status", "unknown") + f" ({run_dir.name})",
                    last_run_dir=str(run_dir),
                    last_images=image_files,
                    last_error="",
                    last_review=aggregate,
                    last_review_path=str(run_dir / "review.scorecard.md"),
                    last_adjusted_prompt=(run_dir / "adjusted_prompt.txt").read_text(encoding="utf-8").strip()
                    if (run_dir / "adjusted_prompt.txt").exists()
                    else "",
                )
                if assign_final:
                    break
                failures += 1
                continue
            stderr = proc.stderr.strip().splitlines()
            error_text = stderr[-1] if stderr else "Unknown error"
            set_state(
                running=False,
                status=f"Generation failed: {error_text}",
                last_run_dir=str(run_dir),
                last_images=image_files,
                last_error=error_text,
            )
            return
        except Exception as exc:
            (run_dir / "ollama.stderr.log").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
            set_state(
                running=False,
                status=f"Generation failed: {type(exc).__name__}: {exc}",
                last_run_dir=str(run_dir),
                last_images=[],
                last_error=str(exc),
            )
            return


def start_review(run_name: str) -> str:
    if get_state()["running"]:
        return "Another workflow action is already in progress."
    run_dir = PROMPTS_DIR / run_name
    if not run_dir.exists():
        return f"Run {run_name} was not found."
    set_state(running=True, status=f"Reviewing {run_name}...", last_run_dir=str(run_dir), last_images=list_image_files(run_dir), last_error="")
    threading.Thread(target=run_review, args=(run_dir,), daemon=True).start()
    return f"Started review for {html.escape(run_name)}."


def run_review(run_dir: Path) -> None:
    try:
        aggregate = perform_review(run_dir)
        adjusted_prompt = ""
        if (run_dir / "adjusted_prompt.txt").exists():
            adjusted_prompt = (run_dir / "adjusted_prompt.txt").read_text(encoding="utf-8").strip()
        set_state(
            running=False,
            status=f"Review {aggregate['review_status']} for {run_dir.name}",
            last_run_dir=str(run_dir),
            last_images=list_image_files(run_dir),
            last_error="",
            last_review=aggregate,
            last_review_path=str(run_dir / "review.scorecard.md"),
            last_adjusted_prompt=adjusted_prompt,
        )
    except Exception as exc:
        (run_dir / "review.error.log").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        set_state(
            running=False,
            status=f"Review failed: {type(exc).__name__}: {exc}",
            last_run_dir=str(run_dir),
            last_images=list_image_files(run_dir),
            last_error=str(exc),
        )


def start_adjust(run_name: str) -> str:
    if get_state()["running"]:
        return "Another workflow action is already in progress."
    run_dir = PROMPTS_DIR / run_name
    if not run_dir.exists():
        return f"Run {run_name} was not found."
    if not (run_dir / "review.scorecard.json").exists():
        return "Run review first so the prompt fixer has scorecard input."
    set_state(running=True, status=f"Adjusting prompt for {run_name}...", last_run_dir=str(run_dir), last_images=list_image_files(run_dir), last_error="")
    threading.Thread(target=run_adjust_prompt, args=(run_dir,), daemon=True).start()
    return f"Started prompt adjustment for {html.escape(run_name)}."


def run_adjust_prompt(run_dir: Path) -> None:
    try:
        module = load_review_module()
        settings = load_run_settings(run_dir)
        fixer_model = settings.get("prompt_fixer_model", DEFAULT_PROMPT_FIXER_MODEL)
        prompt_text = load_run_prompt(run_dir, "prompt.txt")
        scorecard = json.loads((run_dir / "review.scorecard.json").read_text(encoding="utf-8"))
        aggregate = {key: scorecard.get(key, "") for key in ("review_status", "face_lock", "no_text", "style_lock", "notes")}
        verdicts = [module.ReviewVerdict(**reviewer) for reviewer in scorecard.get("reviewers", [])]
        adjusted = module.adjust_prompt(fixer_model, prompt_text, aggregate, verdicts).strip()
        (run_dir / "adjusted_prompt.txt").write_text(adjusted + "\n", encoding="utf-8")
        set_state(
            running=False,
            status=f"Adjusted prompt for {run_dir.name}",
            last_run_dir=str(run_dir),
            last_images=list_image_files(run_dir),
            last_error="",
            last_review=aggregate,
            last_review_path=str(run_dir / "review.scorecard.md"),
            last_adjusted_prompt=adjusted,
        )
    except Exception as exc:
        (run_dir / "adjust.error.log").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        set_state(
            running=False,
            status=f"Prompt adjustment failed: {type(exc).__name__}: {exc}",
            last_run_dir=str(run_dir),
            last_images=list_image_files(run_dir),
            last_error=str(exc),
        )


def retry_run(run_name: str) -> str:
    if get_state()["running"]:
        return "Another workflow action is already in progress."
    run_dir = PROMPTS_DIR / run_name
    if not run_dir.exists():
        return f"Run {run_name} was not found."
    adjusted_prompt_path = run_dir / "adjusted_prompt.txt"
    if not adjusted_prompt_path.exists():
        return "Adjust the prompt first, then retry from the adjusted prompt."
    settings = load_run_settings(run_dir)
    retry_form = {
        "prompt": adjusted_prompt_path.read_text(encoding="utf-8").strip(),
        "steps": settings.get("steps", DEFAULT_STEPS),
        "size": f"{settings.get('width', DEFAULT_SIZE.split('x', 1)[0])}x{settings.get('height', DEFAULT_SIZE.split('x', 1)[1])}",
        "seed": settings.get("seed", ""),
        "negative": settings.get("negative", ""),
        "review_project": settings.get("review_project", str(DEFAULT_REVIEW_PROJECT)),
        "review_models": settings.get("review_models", DEFAULT_REVIEW_MODELS),
        "prompt_fixer_model": settings.get("prompt_fixer_model", DEFAULT_PROMPT_FIXER_MODEL),
    }
    return generate_image(retry_form)


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        clean_path = parsed.path.split("?", 1)[0]
        if self.serve_cockpit_static(parsed):
            return
        if clean_path.startswith("/uploads/"):
            target = UPLOADS_DIR / unquote(clean_path.split("/uploads/", 1)[1])
            self.serve_file(target)
            return
        if clean_path.startswith("/mirrors/"):
            target = IMAGES_DIR / unquote(clean_path.split("/mirrors/", 1)[1])
            self.serve_file(target)
            return
        if clean_path.startswith("/api/"):
            self.handle_api_get(parsed)
            return
        if clean_path == "/legacy":
            self.send_html(render_page())
            return
        if clean_path == "/recent":
            self.send_html(render_recent_page())
            return
        if clean_path.startswith("/open-run/"):
            run_name = clean_path.split("/open-run/", 1)[1]
            run_dir = PROMPTS_DIR / run_name
            if run_dir.exists():
                subprocess.run(["open", str(run_dir)], check=False)
            self.redirect("/")
            return
        if clean_path == "/open-last":
            last_run_dir = str(get_state()["last_run_dir"])
            if last_run_dir:
                subprocess.run(["open", last_run_dir], check=False)
            self.redirect("/")
            return
        if clean_path.startswith("/run-image/"):
            parts = clean_path.split("/", 3)
            if len(parts) == 4:
                _, _, run_name, image_name = parts
                self.serve_file(PROMPTS_DIR / run_name / image_name)
                return
        if clean_path.startswith("/run-artifact/"):
            parts = clean_path.split("/", 3)
            if len(parts) == 4:
                _, _, run_name, artifact_name = parts
                self.serve_file(PROMPTS_DIR / run_name / artifact_name)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        clean_path = parsed.path.split("?", 1)[0]
        if clean_path.startswith("/api/"):
            length = int(self.headers.get("Content-Length", "0"))
            content_type = self.headers.get("Content-Type", "")
            if clean_path == "/api/assets/upload" and "multipart/form-data" in content_type:
                try:
                    form = cgi.FieldStorage(
                        fp=self.rfile,
                        headers=self.headers,
                        environ={
                            "REQUEST_METHOD": "POST",
                            "CONTENT_TYPE": content_type,
                            "CONTENT_LENGTH": str(length),
                        },
                        keep_blank_values=True,
                    )
                    self.handle_api_post(clean_path, None, form)
                except Exception as exc:
                    traceback.print_exc()
                    self.send_json({"error": f"upload failed: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            if "application/json" in content_type:
                data = json.loads(raw or "{}")
            else:
                data = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
            self.handle_api_post(clean_path, data, None)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        data = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
        if clean_path == "/generate":
            self.send_html(render_page(generate_image(data)))
            return
        if clean_path == "/review-run":
            self.send_html(render_page(start_review(data.get("run_name", "").strip())))
            return
        if clean_path == "/adjust-run":
            self.send_html(render_page(start_adjust(data.get("run_name", "").strip())))
            return
        if clean_path == "/retry-run":
            self.send_html(render_page(retry_run(data.get("run_name", "").strip())))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def serve_file(self, path: Path) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".html": "text/html; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".md": "text/markdown; charset=utf-8",
            ".txt": "text/plain; charset=utf-8",
            ".log": "text/plain; charset=utf-8",
        }.get(path.suffix.lower(), "application/octet-stream")
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_cockpit_static(self, parsed: object) -> bool:
        path = getattr(parsed, "path", "/")
        clean = path.split("?", 1)[0]
        if clean in ("/", "/cockpit"):
            self.serve_file(COCKPIT_DIR / "index.html")
            return True
        candidate = clean.lstrip("/")
        if not candidate:
            self.serve_file(COCKPIT_DIR / "index.html")
            return True
        target = (COCKPIT_DIR / unquote(candidate)).resolve()
        if not str(target).startswith(str(COCKPIT_DIR.resolve())):
            return False
        if target.is_file():
            self.serve_file(target)
            return True
        return False

    def handle_api_get(self, parsed: object) -> None:
        path = getattr(parsed, "path", "")
        query = parse_qs(getattr(parsed, "query", ""))
        if path == "/api/spreads":
            self.send_json(load_spreads())
            return
        if path == "/api/assets":
            items, _ = self.filter_assets(query)
            self.send_json(items)
            return
        if path == "/api/config/generation":
            self.send_json(load_generation_config())
            return
        if path == "/api/status":
            self.send_json(get_state())
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_api_post(self, path: str, data: dict[str, object] | None, form: cgi.FieldStorage | None) -> None:
        if path == "/api/generate":
            message = generate_image(data or {})
            self.send_json({"message": message})
            return
        if path == "/api/spreads" and data:
            spread_id = data.get("spread_id")
            if spread_id:
                updated = patch_spread(spread_id, data)
                self.send_json(updated)
                return
        if path.startswith("/api/spreads/"):
            spread_id = path.split("/api/spreads/", 1)[1]
            try:
                updated = patch_spread(spread_id, data or {})
                self.send_json(updated)
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/assets/upload" and form:
            self.handle_asset_upload(form)
            return
        if path == "/api/assets" and data:
            asset_id = data.get("asset_id") or f"asset-{int(datetime.now().timestamp())}"
            asset = {
                "asset_id": asset_id,
                "label": data.get("label", "Custom asset"),
                "source_type": data.get("source_type", "upload"),
                "mirror_url": data.get("mirror_url", ""),
                "spread_ids": data.get("spread_ids", []),
                "timestamp": datetime.now().isoformat(),
            }
            add_asset(asset)
            self.send_json(asset)
            return
        if path == "/api/config/generation" and data:
            save_generation_config(data)
            self.send_json(data)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_asset_upload(self, form: cgi.FieldStorage) -> None:
        file_field = form["file"] if "file" in form else None
        if file_field is None or not getattr(file_field, "filename", ""):
            self.send_json({"error": "file is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        filename = Path(file_field.filename).name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dest = UPLOADS_DIR / f"{timestamp}-{filename}"
        with dest.open("wb") as fh:
            shutil.copyfileobj(file_field.file, fh)
        asset_id = f"upload-{timestamp}"
        spread_id = form.getvalue("spread_id", "").strip()
        asset = {
            "asset_id": asset_id,
            "label": form.getvalue("label", filename),
            "source_type": "upload",
            "mirror_url": f"/uploads/{dest.name}",
            "spread_ids": [spread_id] if spread_id else [],
            "timestamp": datetime.now().isoformat(),
        }
        add_asset(asset)
        if spread_id:
            patch_spread(spread_id, {"assigned_image_id": asset_id})
        self.send_json(asset)

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def filter_assets(self, query: dict[str, list[str]]) -> tuple[list[dict[str, object]], int]:
        items = load_assets()
        spread_filters = query.get("spread", [])
        source_filters = query.get("source", [])
        search_filters = query.get("search", [])
        if spread_filters:
            items = [item for item in items if any(spread in (item.get("spread_ids") or []) for spread in spread_filters)]
        if source_filters:
            items = [item for item in items if item.get("source_type") in source_filters]
        if search_filters:
            needle = search_filters[0].lower()
            items = [
                item
                for item in items
                if needle in (item.get("label") or "").lower() or needle in (item.get("asset_id") or "").lower()
            ]
        try:
            offset = int(query.get("offset", ["0"])[0])
        except ValueError:
            offset = 0
        try:
            limit = int(query.get("limit", ["20"])[0])
        except ValueError:
            limit = 20
        limit = max(1, limit)
        total = len(items)
        return items[offset : offset + limit], total

    def send_html(self, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        with Path("/tmp/image-gen-dashboard-http.log").open("a", encoding="utf-8") as fh:
            fh.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))


def main() -> None:
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/"
    (BASE_DIR / ".dashboard-url").write_text(url, encoding="utf-8")
    load_spreads()
    load_assets()
    load_generation_config()
    server = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    subprocess.run(["open", url], check=False)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
