#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = REPO_ROOT / "image-gen"
MANIFEST_PATH = APP_ROOT / "project-requirements.json"
GENERATION_CONFIG_PATH = REPO_ROOT / "config" / "generation.json"
MAC_APP_OLLAMA = Path("/Applications/Ollama.app/Contents/Resources/ollama")


@dataclass
class CheckResult:
    level: str
    label: str
    detail: str


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_generation_config() -> dict:
    try:
        payload = json.loads(GENERATION_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def find_ollama_binary() -> Path | None:
    discovered = shutil.which("ollama")
    if discovered:
        return Path(discovered)
    if MAC_APP_OLLAMA.exists():
        return MAC_APP_OLLAMA
    return None


def canonical_model_name(name: str) -> str:
    return name.split(":", 1)[0]


def installed_models(ollama_bin: Path) -> tuple[set[str], str]:
    proc = subprocess.run(
        [str(ollama_bin), "list"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = summarize_error(proc.stderr or proc.stdout or "ollama list failed")
        raise RuntimeError(detail)
    names: set[str] = set()
    for line in proc.stdout.splitlines()[1:]:
        parts = line.split()
        if parts:
            names.add(parts[0].strip())
    return names, proc.stdout


def model_present(requested: str, installed: set[str]) -> bool:
    if requested in installed:
        return True
    requested_base = canonical_model_name(requested)
    return any(canonical_model_name(name) == requested_base for name in installed)


def check_paths(manifest: dict) -> list[CheckResult]:
    results: list[CheckResult] = []
    paths = manifest.get("paths", {})
    for raw_path in paths.get("must_exist", []):
        path = Path(raw_path)
        if path.exists():
            results.append(CheckResult("PASS", "Path exists", str(path)))
        else:
            results.append(CheckResult("FAIL", "Missing path", str(path)))
    for raw_path in paths.get("important_files", []):
        path = Path(raw_path)
        if path.is_file():
            results.append(CheckResult("PASS", "File present", str(path)))
        else:
            results.append(CheckResult("FAIL", "Missing file", str(path)))
    for raw_path in paths.get("must_be_writable", []):
        path = Path(raw_path)
        if path.exists() and path.is_dir() and os_access_write(path):
            results.append(CheckResult("PASS", "Writable path", str(path)))
        elif not path.exists():
            results.append(CheckResult("FAIL", "Writable path missing", str(path)))
        else:
            results.append(CheckResult("FAIL", "Path not writable", str(path)))
    return results


def os_access_write(path: Path) -> bool:
    return path.exists() and os_access(path)


def os_access(path: Path) -> bool:
    return os.access(path, os.W_OK)


def summarize_error(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Unknown error"
    return " | ".join(lines[:3])


def check_model_runtime(ollama_bin: Path, model_name: str, timeout: int = 15) -> CheckResult:
    try:
        proc = subprocess.run(
            [str(ollama_bin), "show", model_name],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult("FAIL", "Generator runtime unhealthy", f"{model_name} timed out during `ollama show`.")
    except (subprocess.SubprocessError, OSError) as exc:
        return CheckResult("FAIL", "Generator runtime unhealthy", f"{model_name}: {exc}")
    if proc.returncode != 0:
        return CheckResult(
            "FAIL",
            "Generator runtime unhealthy",
            f"{model_name}: {summarize_error(proc.stderr or proc.stdout or 'Runtime health check failed')}",
        )
    return CheckResult("PASS", "Generator runtime healthy", model_name)


def normalize_generator_backend(value: object) -> str:
    text = str(value or "").strip().lower()
    return text or "comfyui"


def zimage_local_config(generation_config: dict) -> dict:
    value = generation_config.get("zimage_local")
    return value if isinstance(value, dict) else {}


def path_result(label: str, path_value: object, *, required: bool = True) -> CheckResult:
    raw = str(path_value or "").strip()
    if not raw:
        level = "FAIL" if required else "WARN"
        return CheckResult(level, label, "Not configured")
    path = Path(raw).expanduser()
    if path.exists():
        return CheckResult("PASS", label, str(path))
    level = "FAIL" if required else "WARN"
    return CheckResult(level, label, str(path))


def check_zimage_local(generation_config: dict) -> list[CheckResult]:
    config = zimage_local_config(generation_config)
    return [
        path_result("stable-diffusion.cpp binary", config.get("binary_path")),
        path_result("Z-Image-Turbo GGUF diffusion model", config.get("diffusion_model")),
        path_result("Qwen3-4B-Instruct-2507 GGUF text encoder", config.get("text_encoder")),
        path_result("Z-Image ae.safetensors VAE", config.get("vae")),
    ]


def check_ollama(manifest: dict, generation_config: dict) -> list[CheckResult]:
    results: list[CheckResult] = []
    ollama_bin = find_ollama_binary()
    if not ollama_bin:
        return [CheckResult("FAIL", "Ollama missing", "Could not find `ollama` on PATH or at the standard macOS app location.")]

    results.append(CheckResult("PASS", "Ollama binary", str(ollama_bin)))
    try:
        installed, _raw_output = installed_models(ollama_bin)
    except RuntimeError as exc:
        results.append(CheckResult("FAIL", "Ollama list failed", str(exc)))
        return results

    selected_backend = normalize_generator_backend(generation_config.get("generator_backend"))
    required_models = []
    models = manifest.get("models", {})
    for bucket in ("generator", "review", "prompt_fixer"):
        required_models.extend(models.get(bucket, []))

    for model in required_models:
        name = model.get("name", "")
        role = str(model.get("role", "")).strip()
        required = bool(model.get("required", False))
        if not name:
            continue
        if selected_backend == "zimage_local" and role.startswith("image_generation_local_"):
            continue
        if selected_backend == "zimage_local" and role in {
            "image_generation_checkpoint",
            "image_generation_backend",
            "image_generation_compat",
        }:
            continue
        if model_present(name, installed):
            results.append(CheckResult("PASS", "Model present", name))
            if role == "image_generation":
                results.append(check_model_runtime(ollama_bin, name))
        elif required:
            results.append(CheckResult("FAIL", "Model missing", name))
    return results


def summarize(results: list[CheckResult]) -> int:
    failed = [item for item in results if item.level == "FAIL"]
    passed = [item for item in results if item.level == "PASS"]

    print("Image Gen setup check")
    print(f"Manifest: {MANIFEST_PATH}")
    print("")
    for item in results:
        print(f"[{item.level}] {item.label}: {item.detail}")

    print("")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("")
        print("Next actions:")
        for item in failed:
            if item.label == "Model missing":
                print(f"- Install with: ollama pull {item.detail}")
            else:
                print(f"- Fix: {item.detail}")
        return 1
    return 0


def main() -> int:
    if not MANIFEST_PATH.is_file():
        print(f"Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1
    manifest = load_manifest()
    generation_config = load_generation_config()
    results: list[CheckResult] = []
    results.extend(check_paths(manifest))
    if normalize_generator_backend(generation_config.get("generator_backend")) == "zimage_local":
        results.extend(check_zimage_local(generation_config))
    results.extend(check_ollama(manifest, generation_config))
    return summarize(results)


if __name__ == "__main__":
    raise SystemExit(main())
