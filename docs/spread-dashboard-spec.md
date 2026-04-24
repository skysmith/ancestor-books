# Spread-Based Dashboard Spec

## Goal
Create a two-tab cockpit (Generate + Layout) that shares a single spread/page data model. Every view and control writes back to the same underlying JSON/data files so the Layout storyboard, the Generate form, and the Assets catalog always stay in sync and you never have to hunt for separate prompt folders or random files.

Note:

- The active implementation has evolved into a three-tab cockpit: `Layout`, `Generate`, and `Assets`.
- The current frontend lives in `image-gen/cockpit/`.
- Treat this document as product/spec guidance; use `image-gen/README.md` for the current operator-facing workflow.

## Data Model & Persistence
- Store spreads in `data/spreads.json`. Each record contains:
  ```json
  {
    "spread_id": "spread-01",
    "left_page": 2,
    "right_page": 3,
    "title": "Introduction",
    "text_left": "First page copy...",
    "text_right": "Second page copy...",
    "layout_type": "span", // left-page/right-page/full-spread/spot/text-only
    "text_overlay": {
      "visible": true,
      "x": 12,
      "y": 72,
      "width_pct": 65,
      "alignment": "left",
      "wash_opacity": 0.5,
      "margin": 24
    },
    "prompt": "A painterly child-friendly illustration...",
    "negative_prompt": "no text, no logo",
    "seed": 123456,
    "assigned_image_id": "asset-20260315-001",
    "status": "draft",
    "notes": "Needs darker sky",
    "prompt_status": "approved",
    "last_updated_ts": "2026-03-15T12:05:00Z"
  }
  ```
- Assets live in `data/assets.json` with fields like `asset_id`, `source_type` (`upload` or `run`), `file_path`, `prompt`, `seed`, `spread_ids`, `judge_status`, and `mirror_paths` (links into `image-gen/outputs/images`). Spreads reference assets through `assigned_image_id`, while assets track the spreads they serve.
- Helper modules in the prototype will expose `load_spreads()`, `save_spread(spread_id, updates)`, `load_asset(asset_id)`, `link_asset_to_spread(...)`, etc., making it trivial to swap JSON for SQLite later with the same schema.

## Layout Tab
- The storyboard grid shows all spreads as tiles (two-column layout). Each tile displays `left_page‑right_page`, a miniature image preview (from the asset if assigned), a one-line excerpt, and a status badge (`Draft`, `Needs Work`, `Approved`, `Missing`). Tile borders encode `layout_type` (e.g., blue for span, amber for single). A red dot marks missing prompts or images.
- Clicking a tile opens a detail drawer without leaving the grid. The drawer content:
  - Larger preview with left/right page indicators and a “Full-screen spread view” toggle.
  - Drag-and-drop target + buttons for “Upload art”, “Launch generator”, “Choose existing asset”, and “Clear assignment”.
  - Placement toggle (`Left`, `Right`, `Span`, `Inset`) so you explicitly set where the image sits instead of inferring from its aspect ratio.
  - Prompt editor (prompt, negative prompt, seed, prompt status) that writes directly to the spread record.
  - Text overlay controls (visibility toggle, X/Y offsets, width %, alignment, wash opacity, safe margins). Live preview mimics Canva-style overlays so you can nudge the text layer around the current art.
  - Notes/status controls (multi-line notes, status dropdown) and a minute-by-minute history snippet showing when this spread was last edited.
- Zoomed-out tile view only shows a caption-like excerpt, while the detail drawer gives full text to avoid clutter.

## Generate Tab
- Always starts by selecting a spread; the prompt fields auto-load the selected spread’s `prompt`, `negative_prompt`, and `seed`. Selecting a different spread flips the context instantly.
- Generation configuration sits beside the prompt form via `config/generation.json`:
  ```json
  {
    "recursive_mode_enabled": true,
    "max_recursive_fails": 3,
    "judge_model": "llama2-70b",
    "judge_threshold": 0.75,
    "judge_timeout_s": 25,
    "prompt_adjustment_strategy": "suggestive",
    "allow_prompt_updates": true
  }
  ```
- Values are editable right in the tab; “Save as default” writes back to `generation.json`, while “Run with overrides” lets you use temporary tweaks without mutating the file.
- Running the generator:
  1. Calls the local Ollama model via the existing `image-gen` tooling, outputting into `image-gen/outputs/prompts/<timestamp>/` and mirror images into `image-gen/outputs/images/`.
  2. Immediately runs the configured judge model. If the score falls below `judge_threshold` and `recursive_mode_enabled` is true, reissues the run (optionally adjusting the prompt if `prompt_adjustment_strategy` says so). This loop stops either when the judge passes or `max_recursive_fails` is hit; the final image is still returned and annotated with `judge_status: "failed"`.
  3. Creates/updates an asset entry pointing to the new image and metadata, then assigns its `asset_id` back onto the spread’s `assigned_image_id` so Layout instantly reflects the new art.
- The UI exposes runtime stats (current fail count, last judge score, last run timestamp) so you can watch the recursive loop progress.

## Full-Screen Reader & Text Overlay
- Detail drawer’s “Full-screen spread view” renders left and right page containers with gutters and a toggle for the overlay. Text is rendered as HTML/CSS layers (not baked into the artwork) so you can reposition it per spread.
- Overlay controls mirror the drawer sliders and also support keyboard nudges; arrow keys modify X/Y offsets, while width percentage and wash opacity help you create safe margins even when the illustration is busy.
- The renderer remembers overlay visibility per spread and supports arrow navigation to move between spreads in full-screen mode.

## Assets & Upload Workflow
- Continue using `image-gen/outputs/prompts/<timestamp>/` for run metadata and `image-gen/outputs/images/` for mirrored previews, but surface them through the shared catalog `data/assets.json`.
- Upload flow:
  - Tile drawer’s preview area accepts drag-and-drop or “Upload art” button to pick a file. Uploads produce a new asset with `source_type=upload`, `file_path` pointing into a managed uploads folder (e.g., `data/uploads/`), and optional metadata.
  - “Choose existing asset” lists entries from `assets.json`, letting you reuse prior renders without re-running generation.
  - “Clear assignment” simply nulls `assigned_image_id` on the spread while leaving the asset intact.
- Assets track all spreads they have been assigned to, supporting multi-spread reuse and letting the Assets tab show usage history.

## Next Steps
1. Build the prototype Layout tab grid + drawer UI using the spread data model so tiles can highlight status, show overlays, and let you upload/assign art.
2. Wire the Generate tab into the existing `image-gen` scripts with the configurable recursive loop, writing assets back to `data/assets.json` and linking spans to spreads.
3. Implement the full-screen reader view with overlay controls and keyboard navigation.
4. Create helper scripts that manage `spreads.json`, `assets.json`, and `generation.json` so the UI doesn’t have to parse raw directories when iterating.
