# Image Gen Dashboard

Local spread-based illustration cockpit for `ancestor-books`.

This workspace lives at [`/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen) and is now the active home for:

- spread storyboard review
- local image generation through Ollama
- uploaded/generated asset assignment
- recursive judge-and-retry generation settings

## Launch

Preferred launchers:

- [`Image Gen Dashboard.app`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/Image%20Gen%20Dashboard.app)
- [`Launch Image Gen.command`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/Launch%20Image%20Gen.command)
- [`launch_dashboard.sh`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/launch_dashboard.sh)

Main backend entry point:

- [`dashboard.py`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/dashboard.py)

Launcher notes:

- The packaged app now opens the local `.command` launcher instead of trying to execute the shell script directly.
- Older references to `/Users/sky/.openclaw/workspace/image-gen/...` or `/lab/media/image-gen/...` are stale and should be ignored.
- The dashboard writes its current local URL to [`image-gen/.dashboard-url`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/.dashboard-url).

## Cockpit Overview

Frontend files live in [`image-gen/cockpit/`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit):

- [`cockpit/index.html`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/index.html)
- [`cockpit/app.js`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/app.js)
- [`cockpit/style.css`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/style.css)

The UI centers on three tabs:

### Layout

- Storyboard tiles show spread title, page range, preview, excerpt, status, and layout type.
- Single-click selects a spread and focuses the detail drawer.
- Double-click, `Enter`, or `Space` on a tile opens full-screen spread view.
- The right drawer is the main working area for:
  - previewing assigned art
  - drag/drop or button-based uploads
  - launching generation for the selected spread
  - assigning/clearing assets
  - setting placement mode (`left`, `right`, `span`, `inset`)
  - editing prompt, negative prompt, seed, notes, and status
  - positioning draggable text overlays in preview and full-screen modes

### Generate

- Always operates on the currently selected spread.
- Uses the same prompt, negative prompt, and seed as the layout drawer.
- Supports recursive local generation settings including:
  - judge model
  - threshold
  - max recursive fails
  - prompt adjustment strategy
  - allow prompt updates
- Calls the local generator through `/api/generate`, then reviews results and can recurse until pass or max failures.

### Assets

- Lists uploaded and generated assets from the shared asset catalog.
- Lets you assign an asset back to the selected spread.
- Shows run metadata like judge status, attempt count, and artifact links when available.

## Data Files

The dashboard shares one local data model:

- [`data/spreads.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/data/spreads.json)
- [`data/assets.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/data/assets.json)
- [`data/generation.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/data/generation.json)
- [`data/uploads/`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/data/uploads)

What they do:

- `spreads.json` stores spread metadata, prompt fields, status, assignment, and text overlay settings.
- `assets.json` stores uploaded/generated asset records and spread relationships.
- `generation.json` stores default recursive generation settings.
- `data/uploads/` holds uploaded files managed by the dashboard.

## Output Layout

Generated runs continue to land in:

- [`outputs/prompts/`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/outputs/prompts)
- [`outputs/images/`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/outputs/images)

Per-run folder contents:

- `prompt.txt`
- `negative_prompt.txt`
- `settings.json`
- `metadata.json`
- `images.json`
- Ollama logs
- generated image artifacts

Mirror behavior:

- each run keeps its own timestamped prompt folder
- generated images are also copied into `outputs/images/` for quick browsing
- generated/uploaded assets are registered in `assets.json` and can be reassigned from the cockpit

## Recent Changes

- `/api/assets` is now tolerated by the frontend whether it returns a plain array or an `{items, total}` object shape.
- Storyboard workflow now favors tile-first navigation:
  - single-click selects
  - double-click opens full-screen
  - each tile exposes an `Open spread` action
- macOS launchers were updated to route through the local project folder instead of stale external paths.
- Upload flow now includes inline status text in the layout drawer so failures are visible instead of silent.

## Known Focus Areas

Current work is centered on tightening the storyboard workflow:

- make spread review and full-screen editing feel faster
- keep generation results tightly tied to the selected spread
- improve upload and assignment feedback

If behavior seems wrong, check these first:

- the active launcher is the copy inside this folder, not an older app elsewhere
- the dashboard URL in `.dashboard-url` matches the running local server
- the selected spread in Layout and Generate is the same one you expect
