# Image Gen Agents

## Context
This folder anchors the `ancestor-books` generation workflow that used to live under `/lab/media/image-gen`. Treat this clone as the canonical home for the dashboard, image outputs, and review automation.

## Instructions
- Always run `personal/projects/ancestor-books/image-gen/launch_dashboard.sh` (or the `.app` launcher) so the server writes into `outputs/prompts/` and `outputs/images/` inside ancestor-books rather than the old lab tree.
- Prefer the `image-gen/outputs/prompts/<timestamp>/` bundle when picking up prompts, metadata, or scorecards for review; use `outputs/images/` only for quick browsing or approved exports.
- Do not copy files back into `/lab/media/image-gen`; the legacy location is deprecated and may be removed.
