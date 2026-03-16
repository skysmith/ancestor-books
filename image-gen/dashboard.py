#!/usr/bin/env python3
from __future__ import annotations

import cgi
import html
import importlib.util
import json
import os
import random
import re
import signal
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen


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
CURRENT_PROJECT_FILE = DATA_DIR / "dashboard-project.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MANUSCRIPT_UPLOADS_DIR = DATA_DIR / "manuscript-sources"
MANUSCRIPT_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
INBOX_DIR = BASE_DIR / "inbox"
INBOX_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR = WORKSPACE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
GENERATION_CONFIG_FILE = CONFIG_DIR / "generation.json"
PROJECT_REQUIREMENTS_FILE = BASE_DIR / "project-requirements.json"
SETUP_DOCTOR_SCRIPT = WORKSPACE_DIR / "scripts" / "check_image_gen_setup.py"
CUSTOM_PROJECTS_FILE = DATA_DIR / "dashboard-projects.json"
OLLAMA_API = os.environ.get("OLLAMA_API", "http://127.0.0.1:11434/api/generate")

PROJECTS_DIR = WORKSPACE_DIR / "projects"
GENERATED_PROJECTS_DIR = PROJECTS_DIR / "generated"
DASHBOARD_PROJECTS = {
    "book-01": {
        "id": "book-01",
        "label": "Book 1: Night of Courage",
        "path": PROJECTS_DIR / "01-captain-daniel-and-the-night-of-courage",
    },
    "book-02": {
        "id": "book-02",
        "label": "Book 2: The Hungry Winter",
        "path": PROJECTS_DIR / "02-the-hungry-winter",
    },
    "book-03": {
        "id": "book-03",
        "label": "Book 3: The Watchful Dog",
        "path": PROJECTS_DIR / "03-the-watchful-dog",
    },
    "book-04": {
        "id": "book-04",
        "label": "Book 4: The Tory's Honey",
        "path": PROJECTS_DIR / "04-the-torys-honey",
    },
}


def manuscript_links_file(project_id: str) -> Path:
    return MANUSCRIPT_UPLOADS_DIR / project_id / "_links.json"


def load_manuscript_links(project_id: str) -> list[dict[str, object]]:
    return _read_json(manuscript_links_file(project_id), [])


def save_manuscript_links(project_id: str, items: list[dict[str, object]]) -> None:
    path = manuscript_links_file(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, items)

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
            "x": 7,
            "y": 78,
            "width": 86,
            "alignment": "center",
            "wash_opacity": 0.72,
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
    "judge_model": "llava:latest",
    "judge_threshold": 0.78,
    "max_recursive_fails": 3,
    "prompt_adjustment_strategy": "suggestive",
    "allow_prompt_updates": True,
}
DEFAULT_MANUSCRIPT_GENERATION_CONFIG = {
    "provider": "openai",
    "openai_model": "gpt-5.2",
    "local_model": "llama3.2:3b",
    "api_key": "",
    "use_env_api_key": True,
    "openai_base_url": "https://api.openai.com/v1",
}
MANUSCRIPT_GENERATION_FILE = CONFIG_DIR / "manuscript-generation.json"
JUDGE_PRESET_THRESHOLDS = {
    1: 0.62,
    2: 0.72,
    3: 0.78,
    4: 0.86,
    5: 0.93,
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
MANUSCRIPT_STATE = {
    "running": False,
    "status": "Ready",
    "last_error": "",
    "last_project_id": "",
    "last_provider": "",
    "updated_at": "",
}
ABORT_EVENT = threading.Event()
CURRENT_WORKFLOW_PROC: subprocess.Popen[str] | None = None
LOCK = threading.Lock()
REVIEW_MODULE = None
MAGIC_BOOK_THREAD: threading.Thread | None = None


def list_ollama_models() -> list[dict[str, str]]:
    ollama_path = Path(OLLAMA_BIN)
    if not ollama_path.exists():
        return []
    try:
        proc = subprocess.run(
            [str(ollama_path), "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    lines = [line.rstrip() for line in proc.stdout.splitlines() if line.strip()]
    if len(lines) <= 1:
        return []
    items: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        item = {"name": name}
        if len(parts) > 1:
            item["id"] = parts[1]
        if len(parts) > 2:
            item["size"] = parts[2]
        if len(parts) > 3:
            item["modified"] = " ".join(parts[3:])
        items.append(item)
    return items


def _normalize_model_name(value: str) -> str:
    clean = (value or "").strip().lower()
    if clean.endswith(":latest"):
        clean = clean[: -len(":latest")]
    return clean


def summarize_error_text(text: str, max_lines: int = 3) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return "Unknown error"
    return " | ".join(lines[:max_lines])


def find_ollama_binary() -> Path | None:
    configured = Path(OLLAMA_BIN)
    if configured.exists():
        return configured
    discovered = shutil.which("ollama")
    if discovered:
        return Path(discovered)
    return None


def list_ollama_model_names_with_status() -> tuple[list[str], str | None]:
    ollama_path = find_ollama_binary()
    if not ollama_path:
        return [], "Could not find `ollama` on PATH or at the standard macOS app location."
    try:
        proc = subprocess.run(
            [str(ollama_path), "list"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return [], str(exc)
    if proc.returncode != 0:
        return [], summarize_error_text(proc.stderr or proc.stdout)
    lines = [line.rstrip() for line in proc.stdout.splitlines() if line.strip()]
    if len(lines) <= 1:
        return [], None
    names: list[str] = []
    for line in lines[1:]:
        parts = line.split()
        if parts:
            names.append(parts[0].strip())
    return names, None


def model_name_present(requested: str, installed_names: list[str]) -> bool:
    requested_norm = _normalize_model_name(requested)
    return any(_normalize_model_name(name) == requested_norm for name in installed_names)


def load_project_requirements() -> dict[str, object]:
    if not PROJECT_REQUIREMENTS_FILE.exists():
        return {}
    try:
        payload = json.loads(PROJECT_REQUIREMENTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_custom_projects() -> dict[str, dict[str, object]]:
    if not CUSTOM_PROJECTS_FILE.exists():
        return {}
    try:
        payload = json.loads(CUSTOM_PROJECTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    projects: dict[str, dict[str, object]] = {}
    for project_id, project in payload.items():
        if not isinstance(project, dict):
            continue
        path_value = project.get("path", "")
        if not path_value:
            continue
        projects[str(project_id)] = {
            "id": str(project.get("id", project_id)),
            "label": str(project.get("label", project_id)),
            "path": Path(str(path_value)),
            "source": str(project.get("source", "custom")),
            "mode": str(project.get("mode", "manual")),
            "created_at": str(project.get("created_at", "")),
        }
    return projects


def save_custom_projects(projects: dict[str, dict[str, object]]) -> None:
    payload: dict[str, dict[str, object]] = {}
    for project_id, project in projects.items():
        payload[project_id] = {
            "id": str(project.get("id", project_id)),
            "label": str(project.get("label", project_id)),
            "path": str(project.get("path", "")),
            "source": str(project.get("source", "custom")),
            "mode": str(project.get("mode", "manual")),
            "created_at": str(project.get("created_at", "")),
        }
    _write_json(CUSTOM_PROJECTS_FILE, payload)


def all_dashboard_projects() -> dict[str, dict[str, object]]:
    combined = {key: value.copy() for key, value in DASHBOARD_PROJECTS.items()}
    combined.update(load_custom_projects())
    return combined


def get_dashboard_project(project_id: str) -> dict[str, object] | None:
    return all_dashboard_projects().get(project_id)


def slugify(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return clean.strip("-") or "magic-book"


def path_status_item(path: Path, require_writable: bool = False) -> dict[str, object]:
    exists = path.exists()
    writable = exists and os.access(path, os.W_OK)
    if not exists:
        status = "missing"
        detail = "Path does not exist yet."
    elif require_writable and not writable:
        status = "warning"
        detail = "Path exists but is not writable by the current process."
    else:
        status = "ready"
        detail = "Available."
    return {
        "path": str(path),
        "exists": exists,
        "writable": writable,
        "status": status,
        "detail": detail,
    }


def get_setup_status() -> dict[str, object]:
    manifest = load_project_requirements()
    models_section = manifest.get("models", {}) if isinstance(manifest.get("models", {}), dict) else {}
    path_section = manifest.get("paths", {}) if isinstance(manifest.get("paths", {}), dict) else {}

    ollama_path = find_ollama_binary()
    installed_model_names, ollama_error = list_ollama_model_names_with_status()

    runtime_items = [
        {
            "name": "python3",
            "status": "ready" if shutil.which("python3") else "missing",
            "detail": shutil.which("python3") or "Could not find `python3` on PATH.",
        },
        {
            "name": "ollama",
            "status": "ready" if ollama_path and not ollama_error else ("warning" if ollama_path else "missing"),
            "detail": str(ollama_path) if ollama_path and not ollama_error else (ollama_error or "Ollama not installed."),
        },
    ]

    model_items: list[dict[str, object]] = []
    for bucket in ("generator", "review", "prompt_fixer"):
        entries = models_section.get(bucket, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name", "")).strip()
            if not name:
                continue
            present = bool(installed_model_names) and model_name_present(name, installed_model_names)
            status = "ready" if present else ("warning" if ollama_error else "missing")
            detail = (
                "Installed locally."
                if present
                else (f"Ollama check failed: {ollama_error}" if ollama_error else "Install with `ollama pull`.")
            )
            model_items.append(
                {
                    "name": name,
                    "role": str(entry.get("role", bucket)).strip() or bucket,
                    "status": status,
                    "detail": detail,
                }
            )

    path_items: list[dict[str, object]] = []
    for raw_path in path_section.get("must_exist", []):
        path_items.append(path_status_item(Path(str(raw_path))))
    writable_paths = {str(path) for path in path_section.get("must_be_writable", [])}
    for item in path_items:
        if item["path"] in writable_paths:
            item.update(path_status_item(Path(item["path"]), require_writable=True))
    for raw_path in path_section.get("important_files", []):
        path = Path(str(raw_path))
        path_items.append(
            {
                "path": str(path),
                "exists": path.is_file(),
                "writable": path.exists() and os.access(path, os.W_OK),
                "status": "ready" if path.is_file() else "missing",
                "detail": "File present." if path.is_file() else "Required file is missing.",
            }
        )

    failures = [item for item in [*runtime_items, *model_items, *path_items] if item.get("status") == "missing"]
    warnings = [item for item in [*runtime_items, *model_items, *path_items] if item.get("status") == "warning"]
    ready = not failures and not warnings
    if ready:
        summary = "Local runtime, required models, and shared paths look ready."
    elif failures:
        summary = f"{len(failures)} required dependency checks still need attention."
    else:
        summary = f"{len(warnings)} setup checks need a quick look before you trust a run."

    return {
        "ready": ready,
        "summary": summary,
        "manifest_path": str(PROJECT_REQUIREMENTS_FILE),
        "doctor_command": f"python3 {SETUP_DOCTOR_SCRIPT}",
        "runtime": runtime_items,
        "models": model_items,
        "paths": path_items,
        "failures": failures,
        "warnings": warnings,
        "checked_at": datetime.now().isoformat(),
    }


def pick_default_judge_model(installed_names: list[str] | None = None) -> str:
    names = installed_names or [item.get("name", "") for item in list_ollama_models()]
    clean_names = [name for name in names if name]
    if not clean_names:
        return DEFAULT_GENERATION_CONFIG["judge_model"]
    preferred = split_review_models(DEFAULT_REVIEW_MODELS)
    for target in preferred:
        target_norm = _normalize_model_name(target)
        for name in clean_names:
            if _normalize_model_name(name) == target_norm:
                return name
    configured_default = DEFAULT_GENERATION_CONFIG["judge_model"]
    configured_norm = _normalize_model_name(configured_default)
    for name in clean_names:
        if _normalize_model_name(name) == configured_norm:
            return name
    return clean_names[0]


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
    payload = _read_json(GENERATION_CONFIG_FILE, DEFAULT_GENERATION_CONFIG)
    if not isinstance(payload, dict):
        payload = dict(DEFAULT_GENERATION_CONFIG)
    normalized = dict(DEFAULT_GENERATION_CONFIG)
    normalized.update(payload)
    installed_names = [item.get("name", "") for item in list_ollama_models()]
    configured_model = str(normalized.get("judge_model", "")).strip()
    if not configured_model:
        normalized["judge_model"] = pick_default_judge_model(installed_names)
    elif installed_names and not any(
        _normalize_model_name(name) == _normalize_model_name(configured_model)
        for name in installed_names
    ):
        normalized["judge_model"] = pick_default_judge_model(installed_names)
    if normalized != payload:
        _write_json(GENERATION_CONFIG_FILE, normalized)
    return normalized


def save_generation_config(config: dict[str, object]) -> dict[str, object]:
    normalized = dict(DEFAULT_GENERATION_CONFIG)
    normalized.update(config)
    installed_names = [item.get("name", "") for item in list_ollama_models()]
    requested_model = str(normalized.get("judge_model", "")).strip()
    if installed_names:
        if not requested_model or not any(
            _normalize_model_name(name) == _normalize_model_name(requested_model)
            for name in installed_names
        ):
            normalized["judge_model"] = pick_default_judge_model(installed_names)
        else:
            for name in installed_names:
                if _normalize_model_name(name) == _normalize_model_name(requested_model):
                    normalized["judge_model"] = name
                    break
    _write_json(GENERATION_CONFIG_FILE, normalized)
    return normalized


def load_manuscript_generation_config() -> dict[str, object]:
    payload = _read_json(MANUSCRIPT_GENERATION_FILE, DEFAULT_MANUSCRIPT_GENERATION_CONFIG)
    if not isinstance(payload, dict):
        payload = dict(DEFAULT_MANUSCRIPT_GENERATION_CONFIG)
    normalized = dict(DEFAULT_MANUSCRIPT_GENERATION_CONFIG)
    normalized.update(payload)
    normalized["provider"] = str(normalized.get("provider", "openai")).strip().lower() or "openai"
    normalized["openai_model"] = str(normalized.get("openai_model", "gpt-5.2")).strip() or "gpt-5.2"
    normalized["local_model"] = str(normalized.get("local_model", DEFAULT_PROMPT_FIXER_MODEL)).strip() or DEFAULT_PROMPT_FIXER_MODEL
    normalized["api_key"] = str(normalized.get("api_key", "")).strip()
    normalized["openai_base_url"] = str(normalized.get("openai_base_url", "https://api.openai.com/v1")).rstrip("/")
    normalized["use_env_api_key"] = bool(normalized.get("use_env_api_key", True))
    if normalized != payload:
        _write_json(MANUSCRIPT_GENERATION_FILE, normalized)
    return normalized


def save_manuscript_generation_config(config: dict[str, object]) -> dict[str, object]:
    normalized = load_manuscript_generation_config()
    normalized.update(config)
    normalized["provider"] = str(normalized.get("provider", "openai")).strip().lower() or "openai"
    normalized["openai_model"] = str(normalized.get("openai_model", "gpt-5.2")).strip() or "gpt-5.2"
    normalized["local_model"] = str(normalized.get("local_model", DEFAULT_PROMPT_FIXER_MODEL)).strip() or DEFAULT_PROMPT_FIXER_MODEL
    normalized["api_key"] = str(normalized.get("api_key", "")).strip()
    normalized["openai_base_url"] = str(normalized.get("openai_base_url", "https://api.openai.com/v1")).rstrip("/")
    normalized["use_env_api_key"] = bool(normalized.get("use_env_api_key", True))
    _write_json(MANUSCRIPT_GENERATION_FILE, normalized)
    return normalized


def manuscript_config_summary(config: dict[str, object]) -> dict[str, object]:
    api_key = str(config.get("api_key", "")).strip()
    env_key = str(os.environ.get("OPENAI_API_KEY", "")).strip()
    provider = str(config.get("provider", "openai")).strip().lower() or "openai"
    openai_ready = bool(api_key or (config.get("use_env_api_key") and env_key))
    local_model = str(config.get("local_model", "")).strip()
    installed_names = [item.get("name", "") for item in list_ollama_models()]
    local_ready = bool(local_model and model_name_present(local_model, installed_names)) if installed_names else bool(local_model)
    return {
        "provider": provider,
        "openai_model": str(config.get("openai_model", "gpt-5.2")).strip() or "gpt-5.2",
        "local_model": local_model,
        "openai_ready": openai_ready,
        "local_ready": local_ready,
        "api_key_source": "env" if not api_key and env_key else ("saved" if api_key else "missing"),
    }


def load_current_project() -> dict[str, object]:
    default = {"project_id": "book-02"}
    payload = _read_json(CURRENT_PROJECT_FILE, default)
    if not isinstance(payload, dict):
        payload = default
    project_id = payload.get("project_id", "book-02")
    projects = all_dashboard_projects()
    project = projects.get(project_id, DASHBOARD_PROJECTS["book-02"])
    return {
        "project_id": project["id"],
        "label": project["label"],
        "path": str(project["path"]),
    }


def save_current_project(project_id: str) -> dict[str, object]:
    projects = all_dashboard_projects()
    project = projects.get(project_id, DASHBOARD_PROJECTS["book-02"])
    payload = {"project_id": project["id"]}
    _write_json(CURRENT_PROJECT_FILE, payload)
    return {
        "project_id": project["id"],
        "label": project["label"],
        "path": str(project["path"]),
    }


def list_dashboard_projects() -> list[dict[str, object]]:
    current = load_current_project()["project_id"]
    projects = []
    for project in all_dashboard_projects().values():
        projects.append(
            {
                "id": project["id"],
                "label": project["label"],
                "path": str(project["path"]),
                "active": project["id"] == current,
                "source": project.get("source", "built-in"),
                "mode": project.get("mode", "manual"),
            }
        )
    return projects


def list_reference_inbox() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for path in sorted(INBOX_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        items.append(
            {
                "id": path.name,
                "label": path.stem,
                "filename": path.name,
                "url": f"/inbox-files/{path.name}",
                "path": str(path),
            }
        )
    return items


def parse_prompt_markdown(prompt_path: Path) -> dict[str, str]:
    if not prompt_path.exists():
        return {"prompt": "", "note": ""}
    text = prompt_path.read_text(encoding="utf-8")
    prompt_match = re.search(r"## First-Pass Prompt\n\n(.*?)(?=\n## |\Z)", text, re.S)
    note_match = re.search(r"## Illustration Note\n\n(.*?)(?=\n## |\Z)", text, re.S)
    return {
        "prompt": (prompt_match.group(1).strip() if prompt_match else ""),
        "note": (note_match.group(1).strip() if note_match else ""),
    }


def split_visual_focus(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,\n;]+", value) if item.strip()]


def parse_story_metadata(body: str) -> tuple[dict[str, object], str]:
    metadata: dict[str, object] = {
        "story_role": "",
        "beat_type": "",
        "spread_intent": "",
        "emotional_state": "",
        "page_turn_tension": False,
        "visual_focus": [],
    }
    lines = body.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        match = re.match(r"^(ROLE|BEAT|SPREAD INTENT|INTENT|PAGE TURN|PAGE-TURN|EMOTIONAL STATE|EMOTION|VISUAL FOCUS):\s*(.*)$", line)
        if not match:
            break
        key = match.group(1)
        value = match.group(2).strip()
        upper_key = key.upper()
        if upper_key == "ROLE":
            metadata["story_role"] = value.lower()
        elif upper_key == "BEAT":
            metadata["beat_type"] = value.lower()
        elif upper_key in {"SPREAD INTENT", "INTENT"}:
            metadata["spread_intent"] = value
        elif upper_key in {"EMOTIONAL STATE", "EMOTION"}:
            metadata["emotional_state"] = value
        elif upper_key in {"PAGE TURN", "PAGE-TURN"}:
            metadata["page_turn_tension"] = value.lower() in {"true", "yes", "y", "1"}
        elif upper_key == "VISUAL FOCUS":
            items = split_visual_focus(value)
            lookahead = idx + 1
            while lookahead < len(lines):
                bullet = lines[lookahead].strip()
                if not bullet.startswith("- "):
                    break
                items.append(bullet[2:].strip())
                lookahead += 1
            metadata["visual_focus"] = [item for item in items if item]
            idx = lookahead - 1
        idx += 1
    remaining = "\n".join(lines[idx:]).strip()
    return metadata, remaining


def parse_dummy_layout(dummy_path: Path) -> tuple[str, list[dict[str, object]]]:
    text = dummy_path.read_text(encoding="utf-8")
    title_match = re.search(r"^# (.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else dummy_path.parent.parent.name.replace("-", " ").title()
    units: list[dict[str, object]] = []
    sections = re.finditer(
        r"### Spread (\d+) \(Pages ([^)]+)\)\n\n(.*?)(?=\n### Spread |\Z)",
        text,
        re.S,
    )
    for match in sections:
        number = int(match.group(1))
        pages = match.group(2).strip()
        body = match.group(3).strip()
        story_metadata, body = parse_story_metadata(body)
        note_match = re.search(r"\*\*Illustration note:\*\* (.+)", body)
        illustration_note = note_match.group(1).strip() if note_match else ""
        if note_match:
            body = re.sub(r"\n?\*\*Illustration note:\*\* .+", "", body).strip()

        if "**Left Page**" in body:
            left_match = re.search(r"\*\*Left Page\*\*\n\n(.*?)(?=\n\*\*Right Page\*\*)", body, re.S)
            right_match = re.search(r"\*\*Right Page\*\*\n\n(.*)$", body, re.S)
            left_text = clean_markdown_text(left_match.group(1) if left_match else "")
            right_text = clean_markdown_text(right_match.group(1) if right_match else "")
            story_text = "\n\n".join(part for part in [left_text, right_text] if part)
            kind = "split"
        else:
            full_match = re.search(r"\*\*Full Spread(?: — Final Page)?\*\*\n\n(.*)$", body, re.S)
            left_text = ""
            right_text = ""
            story_text = clean_markdown_text(full_match.group(1) if full_match else body)
            kind = "full"

        units.append(
            {
                "slug": f"spread-{number:02d}",
                "title": f"Spread {number}",
                "pages": pages,
                "kind": kind,
                "left_text": left_text,
                "right_text": right_text,
                "story_text": story_text,
                "illustration_note": illustration_note,
                "story_role": story_metadata.get("story_role", ""),
                "beat_type": story_metadata.get("beat_type", ""),
                "spread_intent": story_metadata.get("spread_intent", ""),
                "emotional_state": story_metadata.get("emotional_state", ""),
                "page_turn_tension": bool(story_metadata.get("page_turn_tension", False)),
                "visual_focus": story_metadata.get("visual_focus", []),
            }
        )
    return title, units


def story_field_value(candidate: object, fallback: object) -> object:
    if candidate in (None, "", []):
        return fallback
    return candidate


def compute_story_warnings(spreads: list[dict[str, object]]) -> dict[str, list[str]]:
    warnings_by_spread: dict[str, list[str]] = {}
    for index, spread in enumerate(spreads):
        spread_id = str(spread.get("spread_id", "")).strip()
        if not spread_id:
            continue
        warnings: list[str] = []
        story_text = str(spread.get("text_overlay_text", "")).strip()
        word_count = len(re.findall(r"\b[\w'-]+\b", story_text))
        if word_count > 40:
            warnings.append(f"Text is dense for a picture-book spread ({word_count} words).")
        beat_type = str(spread.get("beat_type", "")).strip().lower()
        if beat_type and index >= 2:
            prev = [str(spreads[index - offset].get("beat_type", "")).strip().lower() for offset in (1, 2)]
            if all(item == beat_type for item in prev):
                warnings.append("Beat type repeats three spreads in a row.")
        if not str(spread.get("spread_intent", "")).strip():
            warnings.append("Add a short note about what this spread needs to communicate.")
        warnings_by_spread[spread_id] = warnings
    return warnings_by_spread


def clean_markdown_text(text: str) -> str:
    text = text.replace("**", "").strip()
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def excerpt_for_text(text: str, max_len: int = 88) -> str:
    flat = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if len(flat) <= max_len:
        return flat
    return flat[: max_len - 1].rsplit(" ", 1)[0] + "..."


def project_asset_url(project_id: str, path: Path) -> str:
    rel = path.resolve().relative_to(WORKSPACE_DIR.resolve())
    return f"/project-file/{project_id}/{rel.as_posix()}"


def import_dashboard_project(project_id: str) -> dict[str, object]:
    project = get_dashboard_project(project_id)
    if not project:
        raise ValueError(f"Unknown project {project_id}")
    project_root = project["path"]
    dummy_path = project_root / "manuscript" / "dummy-layout.md"
    title, units = parse_dummy_layout(dummy_path)
    selects_dir = project_root / "storyboard" / "renders" / "selects"
    existing_spreads = {
        str(item.get("spread_id", "")): item
        for item in load_spreads()
        if item.get("project_id") == project_id
    }
    spreads: list[dict[str, object]] = []
    assets: list[dict[str, object]] = []

    for unit in units:
        slug = unit["slug"]
        prompt_path = project_root / "storyboard" / "prompts" / f"{slug}.md"
        prompt_info = parse_prompt_markdown(prompt_path)
        selected_png = selects_dir / f"{slug}-selected.png"
        selected_json = selects_dir / f"{slug}-selected.json"
        if not selected_png.exists():
            selected_png = selects_dir / f"{slug}-v001.png"
        if not selected_json.exists():
            selected_json = selects_dir / f"{slug}-v001.json"
        selected_prompt = ""
        if selected_json.exists():
            try:
                selected_prompt = json.loads(selected_json.read_text(encoding="utf-8")).get("prompt", "")
            except json.JSONDecodeError:
                selected_prompt = ""

        asset_id = None
        asset_preview = ""
        if selected_png.exists():
            asset_id = f"{project_id}-{slug}"
            asset_preview = project_asset_url(project_id, selected_png)
            assets.append(
                {
                    "asset_id": asset_id,
                    "label": f"{project['label']} {slug}",
                    "source_type": "project-select",
                    "mirror_url": asset_preview,
                    "spread_ids": [slug],
                    "timestamp": datetime.fromtimestamp(selected_png.stat().st_mtime).isoformat(),
                    "project_id": project_id,
                    "project_path": str(selected_png),
                }
            )

        page_match = re.match(r"(\d+)\s*-\s*(\d+)", unit["pages"])
        left_page = int(page_match.group(1)) if page_match else 0
        right_page = int(page_match.group(2)) if page_match else left_page
        existing = existing_spreads.get(slug, {})
        spreads.append(
            {
                "spread_id": slug,
                "title": unit["title"],
                "left_page": left_page,
                "right_page": right_page,
                "layout_type": "span",
                "status": "approved" if asset_id else "draft",
                "excerpt": excerpt_for_text(unit["story_text"]),
                "prompt": selected_prompt or prompt_info["prompt"] or unit["illustration_note"],
                "negative_prompt": "no text, no watermark, clean edges",
                "seed": "",
                "assigned_image_id": asset_id,
                "assigned_image_preview": asset_preview,
                "text_overlay_text": unit["story_text"],
                "text_overlay": {
                    "visible": True,
                    "x": 7,
                    "y": 78,
                    "width": 86,
                    "alignment": "center",
                    "wash_opacity": 0.72,
                },
                "notes": unit["illustration_note"],
                "illustration_notes": story_field_value(existing.get("illustration_notes"), unit["illustration_note"]),
                "story_role": story_field_value(existing.get("story_role"), unit.get("story_role", "")),
                "beat_type": story_field_value(existing.get("beat_type"), unit.get("beat_type", "")),
                "spread_intent": story_field_value(existing.get("spread_intent"), unit.get("spread_intent", "")),
                "emotional_state": story_field_value(existing.get("emotional_state"), unit.get("emotional_state", "")),
                "page_turn_tension": bool(story_field_value(existing.get("page_turn_tension"), unit.get("page_turn_tension", False))),
                "visual_focus": story_field_value(existing.get("visual_focus"), unit.get("visual_focus", [])),
                "prompt_status": "approved" if selected_prompt else "draft",
                "last_updated_ts": datetime.now().isoformat(),
                "project_id": project_id,
                "project_title": title,
            }
        )

    save_spreads(spreads)
    save_assets(assets)
    current = save_current_project(project_id)
    return {
        "project": current,
        "spread_count": len(spreads),
        "asset_count": len(assets),
    }


def load_manuscript_view(project_id: str | None = None) -> dict[str, object]:
    current = load_current_project()
    resolved_project_id = project_id or current["project_id"]
    project = get_dashboard_project(resolved_project_id) or get_dashboard_project(current["project_id"]) or DASHBOARD_PROJECTS["book-02"]
    project_root = project["path"]
    manuscript_dir = project_root / "manuscript"
    prompt_dir = project_root / "storyboard" / "prompts"
    current_spreads = [item for item in load_spreads() if item.get("project_id") == project["id"]]
    if not current_spreads:
        current_spreads = load_spreads()

    documents: list[dict[str, object]] = []
    for name in ["manuscript.md", "text-only-layout.md", "dummy-layout.md", "source-outline.md"]:
        path = manuscript_dir / name
        if not path.exists():
            continue
        documents.append(
            {
                "id": path.stem,
                "label": name.replace(".md", "").replace("-", " ").title(),
                "filename": name,
                "path": str(path),
                "content": path.read_text(encoding="utf-8"),
                "kind": "project-manuscript",
            }
        )

    prompt_cards: list[dict[str, object]] = []
    for spread in current_spreads:
        slug = str(spread.get("spread_id", ""))
        prompt_path = prompt_dir / f"{slug}.md"
        prompt_text = ""
        note_text = ""
        if prompt_path.exists():
            prompt_info = parse_prompt_markdown(prompt_path)
            prompt_text = prompt_info.get("prompt", "")
            note_text = prompt_info.get("note", "")
        prompt_cards.append(
            {
                "spread_id": slug,
                "title": str(spread.get("title", slug)).strip() or slug,
                "pages": f"{spread.get('left_page', '')}–{spread.get('right_page', '')}".strip("–"),
                "story_text": str(spread.get("text_overlay_text", "")).strip(),
                "prompt": prompt_text or str(spread.get("prompt", "")).strip(),
                "note": note_text or str(spread.get("notes", "")).strip(),
                "status": str(spread.get("prompt_status", "")).strip(),
                "story_role": str(spread.get("story_role", "")).strip(),
                "beat_type": str(spread.get("beat_type", "")).strip(),
                "spread_intent": str(spread.get("spread_intent", "")).strip(),
                "emotional_state": str(spread.get("emotional_state", "")).strip(),
                "page_turn_tension": bool(spread.get("page_turn_tension", False)),
                "visual_focus": spread.get("visual_focus", []) if isinstance(spread.get("visual_focus", []), list) else [],
                "illustration_notes": str(spread.get("illustration_notes", spread.get("notes", ""))).strip(),
                "illustration_planning_locked": bool(spread.get("illustration_planning_locked", False)),
            }
        )
    warnings_by_spread = compute_story_warnings(prompt_cards)
    for item in prompt_cards:
        item["warnings"] = warnings_by_spread.get(str(item.get("spread_id", "")), [])

    upload_dir = MANUSCRIPT_UPLOADS_DIR / project["id"]
    upload_dir.mkdir(parents=True, exist_ok=True)
    source_files: list[dict[str, object]] = []
    for path in sorted(upload_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        if path.name == "_links.json":
            continue
        suffix = path.suffix.lower()
        preview = text_preview(extract_text_from_source_file(path), 2000)
        source_files.append(
            {
                "id": path.name,
                "label": path.name,
                "filename": path.name,
                "url": f"/manuscript-upload/{project['id']}/{path.name}",
                "kind": suffix.lstrip("."),
                "preview": preview,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            }
        )
    for item in load_manuscript_links(project["id"]):
        source_files.insert(
            0,
            {
                "id": item.get("id", ""),
                "label": item.get("label", item.get("url", "Link")),
                "filename": "",
                "url": item.get("url", ""),
                "kind": sniff_link_kind(str(item.get("url", ""))),
                "preview": item.get("note", ""),
                "modified": item.get("modified", ""),
            },
        )
    manuscript_config = load_manuscript_generation_config()

    return {
        "project": {
            "id": project["id"],
            "label": project["label"],
            "path": str(project_root),
        },
        "documents": documents,
        "prompts": prompt_cards,
        "sources": source_files,
        "generation": {
            "config": manuscript_config,
            "summary": manuscript_config_summary(manuscript_config),
            "status": get_manuscript_state(),
        },
    }


def resolve_manuscript_document(project_id: str, filename: str) -> Path:
    project = get_dashboard_project(project_id)
    if not project:
        raise ValueError(f"Unknown project {project_id}")
    allowed = {
        "manuscript.md",
        "text-only-layout.md",
        "dummy-layout.md",
        "source-outline.md",
    }
    clean_name = Path(filename).name
    if clean_name not in allowed:
        raise ValueError("Unsupported manuscript document")
    path = project["path"] / "manuscript" / clean_name
    if not path.exists():
        raise ValueError("Manuscript document not found")
    return path


def text_preview(text: str, max_chars: int = 2000) -> str:
    clean = text.strip()
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rsplit(" ", 1)[0] + "..."


def sniff_link_kind(url: str) -> str:
    clean = url.strip().lower()
    if "youtube.com" in clean or "youtu.be" in clean:
        return "youtube"
    if clean.endswith(".pdf"):
        return "pdf-link"
    return "link"


def extract_pdf_text(path: Path) -> str:
    commands = [
        ["pdftotext", str(path), "-"],
        ["mdls", "-raw", "-name", "kMDItemTextContent", str(path)],
    ]
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        output = (proc.stdout or "").strip()
        if proc.returncode == 0 and output and output != "(null)":
            return output
    return ""


def extract_rich_text(path: Path) -> str:
    try:
        proc = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return (proc.stdout or "").strip() if proc.returncode == 0 else ""


def extract_text_from_source_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt", ".json", ".csv"}:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    if suffix in {".doc", ".docx", ".rtf", ".html", ".htm"}:
        return extract_rich_text(path)
    if suffix == ".pdf":
        return extract_pdf_text(path)
    return ""


def build_source_bundle(project_id: str) -> tuple[list[dict[str, object]], str]:
    upload_dir = MANUSCRIPT_UPLOADS_DIR / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    sections: list[str] = []
    items: list[dict[str, object]] = []
    project = get_dashboard_project(project_id)
    manuscript_dir = Path(project["path"]) / "manuscript" if project else None
    if manuscript_dir and manuscript_dir.exists():
        for name in ("source-outline.md", "manuscript.md"):
            path = manuscript_dir / name
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                continue
            items.append({"type": "project-manuscript", "label": name, "path": str(path), "text": text})
            sections.append(f"[PROJECT MANUSCRIPT] {name}\nPath: {path}\nText:\n{text_preview(text, 6000)}")
    for item in load_manuscript_links(project_id):
        url = str(item.get("url", "")).strip()
        note = str(item.get("note", "")).strip()
        label = str(item.get("label", url or "Link")).strip() or "Link"
        kind = sniff_link_kind(url)
        items.append({"type": kind, "label": label, "url": url, "text": note})
        sections.append(f"[{kind.upper()}] {label}\nURL: {url}" + (f"\nNotes:\n{note}" if note else ""))
    for path in sorted(upload_dir.iterdir(), key=lambda candidate: candidate.stat().st_mtime, reverse=True):
        if not path.is_file() or path.name == "_links.json":
            continue
        extracted = extract_text_from_source_file(path)
        kind = path.suffix.lower().lstrip(".") or "file"
        items.append({"type": kind, "label": path.name, "path": str(path), "text": extracted})
        section = f"[{kind.upper()} FILE] {path.name}\nPath: {path}"
        if extracted:
            section += f"\nExtracted text:\n{text_preview(extracted, 6000)}"
        sections.append(section)
    return items, "\n\n".join(section for section in sections if section).strip()


def normalize_plan(plan: dict[str, object], title: str, story: str) -> dict[str, object]:
    fallback = fallback_magic_book_plan(title, story)
    spreads = plan.get("spreads", [])
    if not isinstance(spreads, list) or not spreads:
        return fallback
    normalized_spreads: list[dict[str, object]] = []
    for index, spread in enumerate(spreads[:10], start=1):
        if not isinstance(spread, dict):
            continue
        page_left = index * 2
        page_right = page_left + 1
        normalized_spreads.append(
            {
                "title": str(spread.get("title", f"Spread {index}")).strip() or f"Spread {index}",
                "pages": str(spread.get("pages", f"{page_left}-{page_right}")).strip() or f"{page_left}-{page_right}",
                "kind": "full",
                "story_text": str(spread.get("story_text", "")).strip(),
                "illustration_note": str(spread.get("illustration_note", "")).strip(),
                "prompt": str(spread.get("prompt", "")).strip(),
                "story_role": str(spread.get("story_role", "")).strip(),
                "beat_type": str(spread.get("beat_type", "")).strip(),
                "spread_intent": str(spread.get("spread_intent", "")).strip(),
                "emotional_state": str(spread.get("emotional_state", "")).strip(),
                "page_turn_tension": bool(spread.get("page_turn_tension", False)),
                "visual_focus": spread.get("visual_focus", []) if isinstance(spread.get("visual_focus", []), list) else [],
            }
        )
    if len(normalized_spreads) < 4:
        return fallback
    result = dict(fallback)
    result.update(plan)
    result["title"] = str(plan.get("title", title)).strip() or title
    result["polished_story"] = str(plan.get("polished_story", story)).strip() or story
    result["spreads"] = normalized_spreads
    result["spread_count"] = len(normalized_spreads)
    return result


def build_manuscript_prompt(title: str, source_bundle: str, source_count: int) -> str:
    return f"""
You are creating a serious children's storybook manuscript and spread plan from source material.

Return strict JSON with this schema:
{{
  "title": "book title",
  "polished_story": "complete revised manuscript text",
  "tone_notes": "1-3 sentences about tone, audience, and storytelling stance",
  "character_notes": "1-3 sentences covering protagonist, antagonist or opposing force, and emotional engine",
  "spread_count": 10,
  "spreads": [
    {{
      "title": "short spread title",
      "pages": "2-3",
      "kind": "full",
      "story_text": "the actual text that appears on this spread",
      "illustration_note": "visual storytelling note for the artist",
      "prompt": "illustration-ready prompt",
      "story_role": "opening|setup|rising_action|turn|climax|aftermath|resolution|closing_image",
      "beat_type": "environment|dialogue|action|reaction|suspense|object_focus|reflection",
      "spread_intent": "what this spread must accomplish",
      "emotional_state": "short mood note",
      "page_turn_tension": true,
      "visual_focus": ["subject", "environment", "gesture"]
    }}
  ]
}}

Rules:
- Treat this as a serious piece of art, not a generic summary.
- Infer tone from the sources instead of asking for tone settings.
- If the material suggests romance, grief, danger, wonder, humor, or tenderness, let the manuscript quietly reflect that.
- Build a coherent arc with protagonist, opposing force, escalation, climax, and resolution, but do not force a villain if the conflict is internal or situational.
- Preserve factual source details when the source material appears historical or biographical.
- Keep the prose readable aloud and picture-book friendly.
- Make each spread text concise enough to sit on a storybook spread.
- Make illustration prompts specific and cinematic without mentioning typography.
- No markdown, no preface, no explanation, JSON only.

Working title: {title}
Loaded source count: {source_count}

Source material:
{source_bundle or "[No source text could be extracted. Use the available metadata and links.]"}
""".strip()


def openai_responses_generate(prompt: str, config: dict[str, object], timeout: int = 300) -> str:
    api_key = str(config.get("api_key", "")).strip() or (os.environ.get("OPENAI_API_KEY", "").strip() if config.get("use_env_api_key") else "")
    if not api_key:
        raise ValueError("OpenAI API key is missing. Set OPENAI_API_KEY or add one in Manuscript settings.")
    base_url = str(config.get("openai_base_url", "https://api.openai.com/v1")).rstrip("/")
    model = str(config.get("openai_model", "gpt-5.2")).strip() or "gpt-5.2"
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
    }
    request = Request(
        f"{base_url}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    output = body.get("output", [])
    texts: list[str] = []
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    texts.append(str(content.get("text", "")).strip())
    if texts:
        return "\n".join(text for text in texts if text).strip()
    return str(body.get("output_text", "")).strip()


def generate_manuscript_plan(title: str, source_story: str, source_count: int, config: dict[str, object]) -> tuple[dict[str, object], str]:
    provider = str(config.get("provider", "openai")).strip().lower() or "openai"
    prompt = build_manuscript_prompt(title, source_story, source_count)
    if provider == "openai":
        raw = openai_responses_generate(prompt, config)
        return normalize_plan(parse_json_object(raw), title, source_story), "openai"
    raw = ollama_text_generate(str(config.get("local_model", DEFAULT_PROMPT_FIXER_MODEL)).strip() or DEFAULT_PROMPT_FIXER_MODEL, prompt)
    return normalize_plan(parse_json_object(raw), title, source_story), "ollama"


def write_project_plan(project_id: str, title: str, source_story: str, plan: dict[str, object], planner: str) -> dict[str, object]:
    project = get_dashboard_project(project_id)
    if not project:
        raise ValueError(f"Unknown project {project_id}")
    project_root = Path(project["path"])
    dirs = ensure_magic_book_dirs(project_root)
    spreads = plan.get("spreads", [])
    if not isinstance(spreads, list):
        spreads = []
    (dirs["manuscript"] / "source-outline.md").write_text(source_story.strip() + "\n", encoding="utf-8")
    (dirs["manuscript"] / "manuscript.md").write_text(str(plan.get("polished_story", source_story)).strip() + "\n", encoding="utf-8")
    (dirs["manuscript"] / "dummy-layout.md").write_text(format_dummy_layout(title, spreads), encoding="utf-8")
    (dirs["manuscript"] / "text-only-layout.md").write_text(format_text_only_layout(title, spreads), encoding="utf-8")
    (dirs["notes"] / "magic-book.md").write_text(
        (
            f"# {title}\n\n"
            f"- planner: `{planner}`\n"
            f"- spread count: `{len(spreads)}`\n"
            f"- updated: `{datetime.now().isoformat()}`\n"
        ),
        encoding="utf-8",
    )
    for index, spread in enumerate(spreads, start=1):
        (dirs["prompts"] / f"spread-{index:02d}.md").write_text(format_prompt_markdown(spread), encoding="utf-8")
    imported = import_dashboard_project(project_id)
    return {
        "project": imported.get("project"),
        "spread_count": len(spreads),
        "planner": planner,
    }


def run_manuscript_generation(project_id: str) -> None:
    config = load_manuscript_generation_config()
    project = get_dashboard_project(project_id) or get_dashboard_project(load_current_project()["project_id"])
    if not project:
        set_manuscript_state(running=False, status="Project not found.", last_error="Project not found.", last_project_id=project_id)
        return
    source_items, source_story = build_source_bundle(project["id"])
    title = str(project.get("label", "Untitled book")).strip() or "Untitled book"
    if not source_story:
        set_manuscript_state(
            running=False,
            status="Load at least one text source, PDF, or link note before generating.",
            last_error="No readable source material found.",
            last_project_id=project["id"],
            last_provider=str(config.get("provider", "openai")),
        )
        return
    try:
        set_manuscript_state(
            running=True,
            status=f"Generating manuscript for {title}...",
            last_error="",
            last_project_id=project["id"],
            last_provider=str(config.get("provider", "openai")),
        )
        plan, planner = generate_manuscript_plan(title, source_story, len(source_items), config)
        summary = write_project_plan(project["id"], title, source_story, plan, planner)
        set_manuscript_state(
            running=False,
            status=f"Manuscript ready: {summary['spread_count']} spreads updated with {planner}.",
            last_error="",
            last_project_id=project["id"],
            last_provider=planner,
        )
    except Exception as exc:
        set_manuscript_state(
            running=False,
            status=f"Manuscript generation failed: {type(exc).__name__}: {exc}",
            last_error=str(exc),
            last_project_id=project["id"],
            last_provider=str(config.get("provider", "openai")),
        )


def split_story_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def chunk_story(sentences: list[str], parts: int) -> list[str]:
    if not sentences:
        return ["" for _ in range(parts)]
    chunks: list[list[str]] = [[] for _ in range(parts)]
    for idx, sentence in enumerate(sentences):
        chunks[min(idx * parts // max(len(sentences), 1), parts - 1)].append(sentence)
    return [" ".join(chunk).strip() for chunk in chunks]


def parse_json_object(text: str) -> dict[str, object]:
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return {}
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}


def ollama_text_generate(model: str, prompt: str, timeout: int = 300) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = Request(OLLAMA_API, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return str(body.get("response", "")).strip()


def build_magic_book_story_prompt(title: str, brief: str) -> str:
    return f"""
You are writing a complete first-pass children's picture-book story from a short creative brief.

Write a readable story draft that can later be broken into about 10 illustrated spreads.

Rules:
- Return plain text only.
- Write a full story, not an outline.
- Aim for roughly 500-900 words.
- Keep it vivid, emotionally coherent, and suitable for being read aloud.
- Honor the brief's tone, conflict, and genre cues.
- If the brief is sparse, make strong but sensible storytelling choices.
- Do not add commentary, headings, bullets, or JSON.

Requested title: {title}

Creative brief:
{brief}
""".strip()


def fallback_magic_book_story(title: str, brief: str) -> str:
    clean_title = title.strip() or "Magic Book"
    clean_brief = " ".join(brief.strip().split())
    premise = clean_brief or f"A new adventure unfolds in {clean_title}."
    return (
        f"{clean_title} begins with {premise} "
        "At first, the main character does not understand how serious the problem really is, but they feel the change immediately. "
        "Something in the world is off balance, and the cost of doing nothing grows clearer with every step. "
        "Along the way, the hero meets signs of danger, moments of kindness, and a choice that asks for courage instead of comfort. "
        "Each attempt to move forward reveals more about what is being protected, what might be lost, and why the journey matters. "
        "By the middle of the story, hope and fear are both alive at once, and the hero has to decide what kind of person they will be when the dark moment arrives. "
        "The turning point comes when retreat would be easier, but love, loyalty, or duty pushes them to act anyway. "
        "In the climax, the hero faces the central danger directly and succeeds not by brute force alone, but by understanding what truly must be done. "
        "When the danger passes, the world feels changed because the hero is changed. "
        "The ending lands in relief, warmth, and a sense that courage has left a mark that will last."
    ).strip()


def generate_magic_book_story(title: str, brief: str) -> tuple[str, str]:
    prompt = build_magic_book_story_prompt(title, brief)
    try:
        story = ollama_text_generate(DEFAULT_PROMPT_FIXER_MODEL, prompt)
        if len(re.findall(r"\b[\w'-]+\b", story)) >= 180:
            return story.strip(), "llama"
    except Exception:
        pass
    return fallback_magic_book_story(title, brief), "fallback"


def fallback_magic_book_plan(title: str, story: str, spread_count: int = 10) -> dict[str, object]:
    polished_story = story.strip()
    sentences = split_story_sentences(polished_story)
    chunks = chunk_story(sentences or [polished_story], spread_count)
    roles = [
        "opening",
        "setup",
        "rising_action",
        "rising_action",
        "turn",
        "suspense",
        "climax",
        "aftermath",
        "resolution",
        "closing_image",
    ]
    spreads: list[dict[str, object]] = []
    for index, chunk in enumerate(chunks, start=1):
        spread_text = chunk or polished_story or f"Story beat {index}."
        page_left = index * 2
        page_right = page_left + 1
        spreads.append(
            {
                "title": f"Spread {index}",
                "pages": f"{page_left}-{page_right}",
                "kind": "full",
                "story_text": spread_text,
                "illustration_note": f"Show the clearest visual moment from this beat: {spread_text}",
                "prompt": (
                    f"Children's picture-book illustration for '{title}'. {spread_text} "
                    "Painterly storybook art, expressive composition, no visible text, cohesive character continuity."
                ),
                "story_role": roles[min(index - 1, len(roles) - 1)],
                "beat_type": "action" if index not in {1, spread_count} else "environment",
                "spread_intent": f"Advance the story beat for spread {index}.",
                "emotional_state": "warm and adventurous",
                "page_turn_tension": index < spread_count,
                "visual_focus": [spread_text[:90]],
            }
        )
    return {
        "title": title.strip() or "Magic Book",
        "polished_story": polished_story,
        "spread_count": spread_count,
        "spreads": spreads,
    }


def generate_magic_book_plan(title: str, story: str) -> tuple[dict[str, object], str]:
    prompt = f"""
You are planning a children's picture book for a local illustration cockpit.

Return strict JSON with this schema:
{{
  "title": "book title",
  "polished_story": "cleaned manuscript text",
  "spread_count": 10,
  "spreads": [
    {{
      "title": "short spread title",
      "pages": "2-3",
      "kind": "full",
      "story_text": "one concise spread of book text",
      "illustration_note": "visual guidance",
      "prompt": "image prompt for this spread",
      "story_role": "opening|setup|rising_action|turn|climax|aftermath|resolution|closing_image",
      "beat_type": "environment|dialogue|action|reaction|suspense|object_focus|reflection",
      "spread_intent": "what this spread needs to do",
      "emotional_state": "short mood note",
      "page_turn_tension": true,
      "visual_focus": ["subject", "environment"]
    }}
  ]
}}

Rules:
- Plan exactly 10 story spreads.
- Keep the text simple, readable, and not overwritten.
- Optimize for a fun, coherent overnight picture-book draft rather than literary perfection.
- Make image prompts concrete and illustration-ready.
- No markdown, no explanation, JSON only.

Requested title: {title}

Source story:
{story}
""".strip()
    try:
        raw = ollama_text_generate(DEFAULT_PROMPT_FIXER_MODEL, prompt)
        parsed = parse_json_object(raw)
        spreads = parsed.get("spreads", [])
        if isinstance(spreads, list) and len(spreads) >= 4:
            return parsed, "llama"
    except Exception:
        pass
    return fallback_magic_book_plan(title, story), "fallback"


def format_dummy_layout(title: str, spreads: list[dict[str, object]]) -> str:
    blocks = [f"# {title}", "", "Auto-generated overnight dummy layout.", ""]
    for index, spread in enumerate(spreads, start=1):
        blocks.extend(
            [
                f"### Spread {index} (Pages {spread.get('pages', f'{index * 2}-{index * 2 + 1}')})",
                "",
                f"ROLE: {spread.get('story_role', '')}",
                f"BEAT: {spread.get('beat_type', '')}",
                f"SPREAD INTENT: {spread.get('spread_intent', '')}",
                f"EMOTIONAL STATE: {spread.get('emotional_state', '')}",
                f"PAGE TURN: {'true' if spread.get('page_turn_tension') else 'false'}",
                f"VISUAL FOCUS: {', '.join(spread.get('visual_focus', []))}",
                "",
                "**Full Spread**",
                "",
                str(spread.get("story_text", "")).strip(),
                "",
                f"**Illustration note:** {str(spread.get('illustration_note', '')).strip()}",
                "",
            ]
        )
    return "\n".join(blocks).strip() + "\n"


def format_text_only_layout(title: str, spreads: list[dict[str, object]]) -> str:
    blocks = [f"# {title}", "", "Auto-generated text-only layout.", ""]
    for index, spread in enumerate(spreads, start=1):
        blocks.extend(
            [
                f"## Spread {index} ({spread.get('pages', '')})",
                "",
                str(spread.get("story_text", "")).strip(),
                "",
            ]
        )
    return "\n".join(blocks).strip() + "\n"


def format_prompt_markdown(spread: dict[str, object]) -> str:
    return (
        f"# {spread.get('title', 'Spread')}\n\n"
        f"## First-Pass Prompt\n\n{str(spread.get('prompt', '')).strip()}\n\n"
        f"## Illustration Note\n\n{str(spread.get('illustration_note', '')).strip()}\n"
    )


def create_custom_project_record(project_id: str, label: str, path: Path, mode: str) -> dict[str, object]:
    projects = load_custom_projects()
    projects[project_id] = {
        "id": project_id,
        "label": label,
        "path": path,
        "source": "custom",
        "mode": mode,
        "created_at": datetime.now().isoformat(),
    }
    save_custom_projects(projects)
    return projects[project_id]


def save_manuscript_text_source(project_id: str, text: str, label: str = "Magic Book source draft") -> Path:
    upload_dir = MANUSCRIPT_UPLOADS_DIR / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "source-note"
    dest = upload_dir / f"{timestamp}-{slug}.md"
    dest.write_text(text.strip() + "\n", encoding="utf-8")
    return dest


def ensure_magic_book_dirs(project_root: Path) -> dict[str, Path]:
    GENERATED_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "root": project_root,
        "manuscript": project_root / "manuscript",
        "storyboard": project_root / "storyboard",
        "prompts": project_root / "storyboard" / "prompts",
        "renders_selects": project_root / "storyboard" / "renders" / "selects",
        "renders_raw": project_root / "storyboard" / "renders" / "raw",
        "art_references": project_root / "art" / "references",
        "notes": project_root / "notes",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def write_magic_book_project(
    project_id: str,
    title: str,
    brief: str,
    source_story: str,
    plan: dict[str, object],
    planner: str,
    story_planner: str,
) -> dict[str, object]:
    slug = slugify(title)
    project_root = GENERATED_PROJECTS_DIR / slug
    suffix = 2
    while project_root.exists() and (project_root / ".magic-book-id").exists():
        existing_id = (project_root / ".magic-book-id").read_text(encoding="utf-8").strip()
        if existing_id == project_id:
            break
        project_root = GENERATED_PROJECTS_DIR / f"{slug}-{suffix}"
        suffix += 1
    dirs = ensure_magic_book_dirs(project_root)
    spreads = plan.get("spreads", [])
    if not isinstance(spreads, list):
        spreads = []

    (project_root / ".magic-book-id").write_text(project_id + "\n", encoding="utf-8")
    (dirs["manuscript"] / "source-brief.md").write_text(brief.strip() + "\n", encoding="utf-8")
    (dirs["manuscript"] / "source-story.md").write_text(source_story.strip() + "\n", encoding="utf-8")
    (dirs["manuscript"] / "manuscript.md").write_text(str(plan.get("polished_story", source_story)).strip() + "\n", encoding="utf-8")
    (dirs["manuscript"] / "dummy-layout.md").write_text(format_dummy_layout(title, spreads), encoding="utf-8")
    (dirs["manuscript"] / "text-only-layout.md").write_text(format_text_only_layout(title, spreads), encoding="utf-8")
    (dirs["notes"] / "magic-book.md").write_text(
        (
            f"# {title}\n\n"
            f"- project id: `{project_id}`\n"
            f"- story planner: `{story_planner}`\n"
            f"- planner: `{planner}`\n"
            f"- spread count: `{len(spreads)}`\n"
            f"- created: `{datetime.now().isoformat()}`\n"
        ),
        encoding="utf-8",
    )
    for index, spread in enumerate(spreads, start=1):
        prompt_path = dirs["prompts"] / f"spread-{index:02d}.md"
        prompt_path.write_text(format_prompt_markdown(spread), encoding="utf-8")

    anchor_source = DEFAULT_REVIEW_PROJECT / "art" / "references" / "daniel-cook-character-sheet.md"
    if anchor_source.exists():
        shutil.copy2(anchor_source, dirs["art_references"] / anchor_source.name)

    return {
        "id": project_id,
        "label": title,
        "path": project_root,
        "spread_count": len(spreads),
        "planner": planner,
    }


def run_magic_book_pipeline(project_id: str, title: str, story: str, overnight_mode: bool) -> None:
    try:
        clear_abort_flag()
        set_state(running=True, status=f"Magic book: drafting source story for {title}", last_error="")
        source_story, story_planner = generate_magic_book_story(title, story)
        set_state(running=True, status=f"Magic book: planning spreads for {title}", last_error="")
        plan, planner = generate_magic_book_plan(title, source_story)
        project_info = write_magic_book_project(project_id, title, story, source_story, plan, planner, story_planner)
        create_custom_project_record(project_id, project_info["label"], project_info["path"], "overnight" if overnight_mode else "manual")
        import_dashboard_project(project_id)
        save_manuscript_text_source(project_id, source_story, "Magic Book source story")
        if not overnight_mode:
            set_state(
                running=False,
                status=f"Magic book ready: {project_info['label']}",
                last_error="",
            )
            return

        project_spreads = [item for item in load_spreads() if item.get("project_id") == project_id]
        generation_defaults = load_generation_config()
        total_spreads = len(project_spreads)
        for index, spread in enumerate(project_spreads, start=1):
            prompt = str(spread.get("prompt", "")).strip()
            if not prompt:
                continue
            set_state(
                running=True,
                status=f"Magic book: rendering spread {index} of {total_spreads} for {project_info['label']}",
                last_error="",
            )
            run_generation(
                prompt=prompt,
                effective_prompt=prompt,
                width=DEFAULT_SIZE.split("x", 1)[0],
                height=DEFAULT_SIZE.split("x", 1)[1],
                steps=DEFAULT_STEPS,
                seed="",
                negative=str(spread.get("negative_prompt", "no text, no watermark, clean edges")).strip(),
                spread_id=str(spread.get("spread_id", "")),
                reference_notes=str(spread.get("reference_notes", "")).strip(),
                reference_images=spread.get("reference_images", []) if isinstance(spread.get("reference_images", []), list) else [],
                recursive_config={
                    "judge_model": generation_defaults.get("judge_model", DEFAULT_GENERATION_CONFIG["judge_model"]),
                    "judge_threshold": generation_defaults.get("judge_threshold", DEFAULT_GENERATION_CONFIG["judge_threshold"]),
                    "max_recursive_fails": generation_defaults.get("max_recursive_fails", DEFAULT_GENERATION_CONFIG["max_recursive_fails"]),
                    "prompt_adjustment_strategy": generation_defaults.get("prompt_adjustment_strategy", DEFAULT_GENERATION_CONFIG["prompt_adjustment_strategy"]),
                    "allow_prompt_updates": generation_defaults.get("allow_prompt_updates", DEFAULT_GENERATION_CONFIG["allow_prompt_updates"]),
                },
                review_project=str(project_info["path"]),
                review_models=split_review_models(DEFAULT_REVIEW_MODELS),
                prompt_fixer_model=DEFAULT_PROMPT_FIXER_MODEL,
            )
            state = get_state()
            if state.get("last_error"):
                return
        set_state(running=False, status=f"Magic book finished: {project_info['label']}", last_error="")
    except Exception as exc:
        set_state(running=False, status=f"Magic book failed: {type(exc).__name__}: {exc}", last_error=str(exc))


def create_magic_book(title: str, story: str, overnight_mode: bool) -> dict[str, object]:
    clean_title = title.strip() or f"Magic Book {datetime.now().strftime('%Y-%m-%d')}"
    clean_story = story.strip()
    if not clean_story:
        raise ValueError("Story text is required to create a magic book.")
    if get_state().get("running"):
        raise ValueError("Another generation workflow is already running. Wait for it to finish first.")
    project_id = f"magic-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(100,999)}"
    slug = slugify(clean_title)
    label = clean_title
    create_custom_project_record(project_id, label, GENERATED_PROJECTS_DIR / slug, "overnight" if overnight_mode else "manual")
    thread = threading.Thread(
        target=run_magic_book_pipeline,
        args=(project_id, clean_title, clean_story, overnight_mode),
        daemon=True,
    )
    thread.start()
    global MAGIC_BOOK_THREAD
    MAGIC_BOOK_THREAD = thread
    return {
        "project_id": project_id,
        "label": label,
        "overnight_mode": overnight_mode,
        "message": "Magic book started. Planning the project now." if overnight_mode else "Magic book project creation started.",
    }


def get_spread(spread_id: str) -> dict[str, object] | None:
    return next((spread for spread in load_spreads() if spread["spread_id"] == spread_id), None)


def patch_spread(spread_id: str, updates: dict[str, object]) -> dict[str, object]:
    spreads = load_spreads()
    assets = load_assets()
    for idx, spread in enumerate(spreads):
        if spread["spread_id"] != spread_id:
            continue
        merged = {**spread}
        normalized_updates = dict(updates)
        if "visual_focus" in normalized_updates:
            visual_focus = normalized_updates.get("visual_focus")
            if isinstance(visual_focus, str):
                normalized_updates["visual_focus"] = split_visual_focus(visual_focus)
            elif not isinstance(visual_focus, list):
                normalized_updates["visual_focus"] = []
        if "page_turn_tension" in normalized_updates:
            value = normalized_updates.get("page_turn_tension")
            if isinstance(value, str):
                normalized_updates["page_turn_tension"] = value.lower() in {"true", "1", "yes", "y", "on"}
            else:
                normalized_updates["page_turn_tension"] = bool(value)
        if "text_overlay" in updates and isinstance(updates["text_overlay"], dict):
            merged["text_overlay"] = {**merged.get("text_overlay", {}), **updates["text_overlay"]}
        if "generation_overrides" in normalized_updates:
            gen_updates = normalized_updates["generation_overrides"]
            if gen_updates is None:
                merged["generation_overrides"] = {}
            elif isinstance(gen_updates, dict):
                merged["generation_overrides"] = {**merged.get("generation_overrides", {}), **gen_updates}
        merged.update(
            {k: v for k, v in normalized_updates.items() if k not in {"text_overlay", "generation_overrides"}}
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
    if abort_requested():
        raise RuntimeError("Aborted by user.")
    module = load_review_module()
    image_path = find_primary_image(run_dir)
    if image_path is None:
        raise RuntimeError(f"No image file found in {run_dir}")
    prompt_text = load_run_prompt(run_dir, "prompt.txt")
    settings = load_run_settings(run_dir)
    project_root = Path(settings.get("review_project", str(DEFAULT_REVIEW_PROJECT))).expanduser()
    review_models = split_review_models(settings.get("review_models", DEFAULT_REVIEW_MODELS))
    installed = module.installed_models()
    verdicts = []
    for model in review_models:
        if abort_requested():
            raise RuntimeError("Aborted by user.")
        verdicts.append(
            module.safe_review_image(
                image_path,
                model,
                prompt_text=prompt_text,
                project_root=project_root,
                installed=installed,
            )
        )
    if abort_requested():
        raise RuntimeError("Aborted by user.")
    aggregate = module.aggregate_reviews(verdicts)
    if abort_requested():
        raise RuntimeError("Aborted by user.")
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


def set_manuscript_state(**kwargs: object) -> None:
    with LOCK:
        MANUSCRIPT_STATE.update(kwargs)
        MANUSCRIPT_STATE["updated_at"] = datetime.now().isoformat()


def get_manuscript_state() -> dict[str, object]:
    with LOCK:
        return dict(MANUSCRIPT_STATE)


def clear_abort_flag() -> None:
    ABORT_EVENT.clear()


def request_abort() -> bool:
    ABORT_EVENT.set()
    proc: subprocess.Popen[str] | None
    with LOCK:
        proc = CURRENT_WORKFLOW_PROC
    if proc and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except OSError:
            try:
                proc.terminate()
            except OSError:
                return False
        return True
    return False


def abort_requested() -> bool:
    return ABORT_EVENT.is_set()


def set_current_workflow_process(proc: subprocess.Popen[str] | None) -> None:
    global CURRENT_WORKFLOW_PROC
    with LOCK:
        CURRENT_WORKFLOW_PROC = proc


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
    reference_notes = form.get("reference_notes", "").strip()
    reference_images: list[dict[str, object]] = []
    if spread_id:
        spread = get_spread(spread_id) or {}
        if not reference_notes:
            reference_notes = str(spread.get("reference_notes", "")).strip()
        raw_refs = spread.get("reference_images", [])
        if isinstance(raw_refs, list):
            reference_images = [item for item in raw_refs if isinstance(item, dict)]

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
    clear_abort_flag()

    width, height = size.split("x", 1)
    effective_prompt = prompt
    if reference_notes:
        effective_prompt = f"{prompt}\n\nReference cues to honor:\n{reference_notes}"
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
            effective_prompt,
            width,
            height,
            steps,
            seed,
            negative,
            spread_id,
            reference_notes,
            reference_images,
            recursive_config,
            review_project,
            review_models,
            prompt_fixer_model,
        ),
        daemon=True,
    ).start()
    return "Started generation."


def run_generation(
    prompt: str,
    effective_prompt: str,
    width: str,
    height: str,
    steps: str,
    seed: str,
    negative: str,
    spread_id: str,
    reference_notes: str,
    reference_images: list[dict[str, object]],
    recursive_config: dict[str, object],
    review_project: str,
    review_models: list[str],
    prompt_fixer_model: str,
) -> None:
    max_fails = max(int(recursive_config.get("max_recursive_fails", 0) or 0), 0)
    attempt = 0
    failures = 0
    while True:
        if abort_requested():
            set_current_workflow_process(None)
            set_state(
                running=False,
                status="Generation aborted.",
                last_error="Aborted by user.",
            )
            return
        attempt += 1
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = PROMPTS_DIR / f"{timestamp}-attempt-{attempt}"
        run_dir.mkdir(parents=True, exist_ok=True)

        (run_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        (run_dir / "effective_prompt.txt").write_text(effective_prompt + "\n", encoding="utf-8")
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
            "reference_notes": reference_notes,
            "reference_images": reference_images,
        }
        (run_dir / "settings.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        metadata_path = run_dir / "metadata.json"
        metadata = {
            "timestamp": timestamp,
            "prompt_file": str(run_dir / "prompt.txt"),
            "effective_prompt_file": str(run_dir / "effective_prompt.txt"),
            "negative_prompt_file": str(run_dir / "negative_prompt.txt"),
            "settings": settings,
            "review_project": review_project,
            "review_models": review_models,
            "prompt_fixer_model": prompt_fixer_model,
            "images": [],
            "spread_id": spread_id,
            "prompt": prompt,
            "effective_prompt": effective_prompt,
            "reference_notes": reference_notes,
            "reference_images": reference_images,
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
            cmd = [OLLAMA_BIN, "run", MODEL, effective_prompt, "--width", width, "--height", height, "--steps", steps]
            if negative:
                cmd.extend(["--negative", negative])
            if seed:
                cmd.extend(["--seed", seed])
            proc = subprocess.Popen(
                cmd,
                cwd=run_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            set_current_workflow_process(proc)
            while proc.poll() is None:
                if abort_requested():
                    try:
                        os.killpg(proc.pid, signal.SIGTERM)
                    except OSError:
                        try:
                            proc.terminate()
                        except OSError:
                            pass
                    break
                time.sleep(0.25)
            stdout, stderr = proc.communicate()
            set_current_workflow_process(None)
            (run_dir / "ollama.stdout.log").write_text(stdout or "", encoding="utf-8")
            (run_dir / "ollama.stderr.log").write_text(stderr or "", encoding="utf-8")
            if abort_requested():
                set_state(
                    running=False,
                    status="Generation aborted.",
                    last_run_dir=str(run_dir),
                    last_images=list_image_files(run_dir),
                    last_error="Aborted by user.",
                )
                return
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
                    if abort_requested():
                        set_state(
                            running=False,
                            status="Generation aborted.",
                            last_run_dir=str(run_dir),
                            last_images=image_files,
                            last_error="Aborted by user.",
                        )
                        return
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
            stderr_lines = (stderr or "").strip().splitlines()
            error_text = stderr_lines[-1] if stderr_lines else "Unknown error"
            set_state(
                running=False,
                status=f"Generation failed: {error_text}",
                last_run_dir=str(run_dir),
                last_images=image_files,
                last_error=error_text,
            )
            return
        except Exception as exc:
            set_current_workflow_process(None)
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
    clear_abort_flag()
    run_dir = PROMPTS_DIR / run_name
    if not run_dir.exists():
        return f"Run {run_name} was not found."
    set_state(running=True, status=f"Reviewing {run_name}...", last_run_dir=str(run_dir), last_images=list_image_files(run_dir), last_error="")
    threading.Thread(target=run_review, args=(run_dir,), daemon=True).start()
    return f"Started review for {html.escape(run_name)}."


def run_review(run_dir: Path) -> None:
    try:
        if abort_requested():
            set_state(
                running=False,
                status="Run killed.",
                last_run_dir=str(run_dir),
                last_images=list_image_files(run_dir),
                last_error="Killed by user.",
            )
            return
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
        if abort_requested() or str(exc) == "Aborted by user.":
            set_state(
                running=False,
                status="Run killed.",
                last_run_dir=str(run_dir),
                last_images=list_image_files(run_dir),
                last_error="Killed by user.",
            )
            return
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
    clear_abort_flag()
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
        if abort_requested():
            set_state(
                running=False,
                status="Run killed.",
                last_run_dir=str(run_dir),
                last_images=list_image_files(run_dir),
                last_error="Killed by user.",
            )
            return
        module = load_review_module()
        settings = load_run_settings(run_dir)
        fixer_model = settings.get("prompt_fixer_model", DEFAULT_PROMPT_FIXER_MODEL)
        prompt_text = load_run_prompt(run_dir, "prompt.txt")
        scorecard = json.loads((run_dir / "review.scorecard.json").read_text(encoding="utf-8"))
        aggregate = {key: scorecard.get(key, "") for key in ("review_status", "face_lock", "no_text", "style_lock", "notes")}
        verdicts = [module.ReviewVerdict(**reviewer) for reviewer in scorecard.get("reviewers", [])]
        if abort_requested():
            set_state(
                running=False,
                status="Run killed.",
                last_run_dir=str(run_dir),
                last_images=list_image_files(run_dir),
                last_error="Killed by user.",
            )
            return
        adjusted = module.adjust_prompt(fixer_model, prompt_text, aggregate, verdicts).strip()
        if abort_requested():
            set_state(
                running=False,
                status="Run killed.",
                last_run_dir=str(run_dir),
                last_images=list_image_files(run_dir),
                last_error="Killed by user.",
            )
            return
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
        if abort_requested() or str(exc) == "Aborted by user.":
            set_state(
                running=False,
                status="Run killed.",
                last_run_dir=str(run_dir),
                last_images=list_image_files(run_dir),
                last_error="Killed by user.",
            )
            return
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
        if clean_path.startswith("/inbox-files/"):
            target = INBOX_DIR / unquote(clean_path.split("/inbox-files/", 1)[1])
            self.serve_file(target)
            return
        if clean_path.startswith("/mirrors/"):
            target = IMAGES_DIR / unquote(clean_path.split("/mirrors/", 1)[1])
            self.serve_file(target)
            return
        if clean_path.startswith("/project-file/"):
            rel_path = unquote(clean_path.split("/project-file/", 1)[1]).split("/", 1)
            if len(rel_path) == 2:
                _, relative = rel_path
                target = (WORKSPACE_DIR / relative).resolve()
                if str(target).startswith(str(WORKSPACE_DIR.resolve())):
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
        if clean.startswith("/manuscript-upload/"):
            candidate = clean.split("/manuscript-upload/", 1)[1].lstrip("/")
            target = (MANUSCRIPT_UPLOADS_DIR / unquote(candidate)).resolve()
            if str(target).startswith(str(MANUSCRIPT_UPLOADS_DIR.resolve())) and target.is_file():
                self.serve_file(target)
                return True
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
        if path == "/api/projects":
            self.send_json({"projects": list_dashboard_projects(), "current": load_current_project()})
            return
        if path == "/api/references":
            self.send_json({"items": list_reference_inbox()})
            return
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
        if path == "/api/manuscript":
            project_id = query.get("project_id", [""])[0].strip() or None
            self.send_json(load_manuscript_view(project_id))
            return
        if path == "/api/manuscript/config":
            config = load_manuscript_generation_config()
            self.send_json({"config": config, "summary": manuscript_config_summary(config)})
            return
        if path == "/api/manuscript/status":
            self.send_json(get_manuscript_state())
            return
        if path == "/api/ollama/models":
            self.send_json({"items": list_ollama_models()})
            return
        if path == "/api/setup-status":
            self.send_json(get_setup_status())
            return
        if path == "/api/status":
            self.send_json(get_state())
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_api_post(self, path: str, data: dict[str, object] | None, form: cgi.FieldStorage | None) -> None:
        if path == "/api/projects/load" and data:
            project_id = str(data.get("project_id", "")).strip()
            try:
                result = import_dashboard_project(project_id)
                self.send_json(result)
            except (ValueError, FileNotFoundError) as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/projects/create" and data:
            try:
                result = create_magic_book(
                    title=str(data.get("title", "")).strip(),
                    story=str(data.get("story", "")).strip(),
                    overnight_mode=bool(data.get("overnight_mode", False)),
                )
                self.send_json(result)
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/generate":
            message = generate_image(data or {})
            self.send_json({"message": message})
            return
        if path == "/api/generate/abort":
            message = "Kill requested."
            aborted = request_abort()
            if get_state().get("running"):
                set_state(status="Killing active run...", last_error="")
            if not aborted and not get_state().get("running"):
                message = "No active run to kill."
            self.send_json({"message": message, "aborted": aborted})
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
        if path == "/api/manuscript/upload" and form:
            self.handle_manuscript_upload(form)
            return
        if path == "/api/manuscript/text" and data:
            self.handle_manuscript_text(data)
            return
        if path == "/api/manuscript/link" and data:
            self.handle_manuscript_link(data)
            return
        if path == "/api/manuscript/document" and data:
            self.handle_manuscript_document(data)
            return
        if path == "/api/manuscript/config" and data:
            config = save_manuscript_generation_config(data)
            self.send_json({"config": config, "summary": manuscript_config_summary(config)})
            return
        if path == "/api/manuscript/generate" and data is not None:
            self.handle_manuscript_generate(data)
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

    def handle_manuscript_upload(self, form: cgi.FieldStorage) -> None:
        file_field = form["file"] if "file" in form else None
        if file_field is None or not getattr(file_field, "filename", ""):
            self.send_json({"error": "file is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        current = load_current_project()
        project_id = form.getvalue("project_id", current["project_id"]).strip() or current["project_id"]
        upload_dir = MANUSCRIPT_UPLOADS_DIR / project_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(file_field.filename).name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dest = upload_dir / f"{timestamp}-{filename}"
        with dest.open("wb") as fh:
            shutil.copyfileobj(file_field.file, fh)
        self.send_json({"message": f"Uploaded {filename}"})

    def handle_manuscript_text(self, data: dict[str, object]) -> None:
        current = load_current_project()
        project_id = str(data.get("project_id", current["project_id"])).strip() or current["project_id"]
        text = str(data.get("text", "")).strip()
        label = str(data.get("label", "")).strip() or "Pasted source"
        if not text:
            self.send_json({"error": "text is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        upload_dir = MANUSCRIPT_UPLOADS_DIR / project_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "source-note"
        dest = upload_dir / f"{timestamp}-{slug}.md"
        dest.write_text(text + "\n", encoding="utf-8")
        self.send_json({"message": f"Saved note {label}"})

    def handle_manuscript_link(self, data: dict[str, object]) -> None:
        current = load_current_project()
        project_id = str(data.get("project_id", current["project_id"])).strip() or current["project_id"]
        url = str(data.get("url", "")).strip()
        label = str(data.get("label", "")).strip() or url
        note = str(data.get("note", "")).strip()
        if not url:
            self.send_json({"error": "url is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        links = [item for item in load_manuscript_links(project_id) if item.get("url") != url]
        links.insert(
            0,
            {
                "id": f"link-{int(datetime.now().timestamp())}",
                "label": label,
                "url": url,
                "note": note,
                "modified": datetime.now().isoformat(),
            },
        )
        save_manuscript_links(project_id, links)
        self.send_json({"message": f"Saved link {label}"})

    def handle_manuscript_document(self, data: dict[str, object]) -> None:
        current = load_current_project()
        project_id = str(data.get("project_id", current["project_id"])).strip() or current["project_id"]
        filename = str(data.get("filename", "")).strip()
        content = str(data.get("content", ""))
        if not filename:
            self.send_json({"error": "filename is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            path = resolve_manuscript_document(project_id, filename)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        self.send_json({"message": f"Saved {path.name}"})

    def handle_manuscript_generate(self, data: dict[str, object]) -> None:
        current = load_current_project()
        project_id = str(data.get("project_id", current["project_id"])).strip() or current["project_id"]
        status = get_manuscript_state()
        if status.get("running"):
            self.send_json({"error": "Manuscript generation is already running."}, status=HTTPStatus.BAD_REQUEST)
            return
        thread = threading.Thread(target=run_manuscript_generation, args=(project_id,), daemon=True)
        thread.start()
        self.send_json({"message": "Generating manuscript from loaded sources."})

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
    current = load_current_project()
    spreads = load_spreads()
    if not spreads or not all(isinstance(item, dict) and item.get("project_id") for item in spreads):
        import_dashboard_project(current["project_id"])
    else:
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
