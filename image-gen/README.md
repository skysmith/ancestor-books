# Image Gen Dashboard

Local spread-based illustration cockpit for `ancestor-books`.

This workspace lives at [`/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen) and is now the active home for:

- spread storyboard review
- local image generation through Ollama
- uploaded/generated asset assignment
- recursive judge-and-retry generation settings
- manuscript generation, editing, and source organization

## Packaging Direction

This project is being boxed up as a local-first, shareable cockpit with local image generation and optional hosted manuscript-generation wiring.

Key idea:

- image generation and review are still local-first
- Ollama remains the runtime dependency for image generation and review
- Manuscript generation can use OpenAI or a local Ollama text model
- required local setup is documented in [`project-requirements.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/project-requirements.json)
- setup can be verified with [`scripts/check_image_gen_setup.py`](/Users/sky/Documents/codex/personal/projects/ancestor-books/scripts/check_image_gen_setup.py)

Run the doctor check:

```bash
python3 /Users/sky/Documents/codex/personal/projects/ancestor-books/scripts/check_image_gen_setup.py
```

Current required local models:

- generator: `x/z-image-turbo:latest`
- review: `llava:latest`
- review: `qwen2.5vl:latest`
- prompt fixer: `llama3.2:3b`

The dashboard now also exposes a lightweight setup summary at `/api/setup-status` and renders it in the `Generate` tab as the `Setup readiness` card.

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

The UI centers on four tabs:

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

Layout art-state labels:

- `Approved` means the spread is backed by a selected render in `storyboard/renders/selects/`.
- `Candidate` means the spread is showing the latest raw render from `storyboard/renders/raw/`, but it has not been promoted yet.
- `Assigned` means some other asset is attached to the spread, such as an uploaded asset or a non-select project asset.
- `Draft` means there is still no image preview for that spread.

Approving a candidate:

- When a spread is showing a raw fallback render, the drawer exposes `Approve candidate`.
- That action copies the latest raw render into `storyboard/renders/selects/` as the spread's selected image, copies its metadata JSON, and copies the scorecard JSON when present.
- After promotion, the tile should switch from `Candidate` to `Approved`.

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
- Includes a `Kill active run` control that is intended to stop the active local generation process and prevent the next retry attempt from starting.

### Assets

- Lists uploaded and generated assets from the shared asset catalog.
- Lets you assign an asset back to the selected spread.
- Shows run metadata like judge status, attempt count, and artifact links when available.

### Manuscript

- Shows the two primary working documents from the selected project:
  - `manuscript.md`
  - `dummy-layout.md`
- Lets you edit those manuscript files inline from the dashboard.
- Treats `dummy-layout.md` as the bridge into `Layout` and `Generate`.
- Includes a `Sync to spreads` action on `Dummy Layout` that re-imports spread data for the current project.
- Lists `Illustration planning` cards alongside source material for review.
- Can now generate a full manuscript + spread plan from loaded source material.
- Includes a `New project` / `Magic Book` flow for creating generated local projects from a story seed.

Manuscript generation notes:

- the `Source material` rail now accepts pasted text, uploaded files, and saved links including YouTube URLs
- the `Illustration planning` column now defaults to:
  - spread text
  - editable image prompt
  - collapsed advanced story-planning fields
- the `Generate manuscript` button aggregates loaded sources and writes back to the current project's:
  - `manuscript/manuscript.md`
  - `manuscript/text-only-layout.md`
  - `manuscript/dummy-layout.md`
  - `storyboard/prompts/spread-*.md`
- OpenAI is optional and configurable from the Manuscript tab
- the current default OpenAI model is `gpt-5.2`
- local fallback is an Ollama text model, defaulting to `llama3.2:3b`
- if someone does not want automatic generation, they can still paste or edit manuscript files manually in the dashboard
- manual prompt edits made in `Illustration planning` update the live spread data used by `Generate`
- `Layout` and `Generate` consume the imported spread data, which is currently rebuilt from `dummy-layout.md`

## Data Files

The dashboard shares one local data model:

- [`data/spreads.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/data/spreads.json)
- [`data/assets.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/data/assets.json)
- [`config/generation.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/config/generation.json)
- [`data/uploads/`](/Users/sky/Documents/codex/personal/projects/ancestor-books/data/uploads)
- [`data/manuscript-sources/`](/Users/sky/Documents/codex/personal/projects/ancestor-books/data/manuscript-sources)

What they do:

- `spreads.json` stores spread metadata, prompt fields, status, assignment, and text overlay settings.
- `assets.json` stores uploaded/generated asset records and spread relationships.
- `generation.json` stores default recursive generation settings.
- `data/uploads/` holds uploaded files managed by the dashboard.
- `data/manuscript-sources/` holds uploaded manuscript/source documents for the Manuscript tab.

Project art sources:

- `storyboard/renders/raw/` contains work-in-progress renders and judge artifacts.
- `storyboard/renders/selects/` contains the currently approved per-spread renders that the layout should treat as locked selections.

Related packaging files:

- [`project-requirements.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/project-requirements.json)
- [`scripts/check_image_gen_setup.py`](/Users/sky/Documents/codex/personal/projects/ancestor-books/scripts/check_image_gen_setup.py)
- [`dashboard.py`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/dashboard.py)
- [`cockpit/app.js`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/app.js)
- [`data/dashboard-projects.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/data/dashboard-projects.json)

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

Practical verification path:

- if you want the full provenance for a generated image, start in the matching run folder under `outputs/prompts/`
- if you just want to quickly inspect the latest generated PNG/JPG files inside this project, use `outputs/images/`
- asset records in `data/assets.json` link the dashboard card back to both the mirrored image and the original run artifact path

## Recent Changes

- `/api/assets` is now tolerated by the frontend whether it returns a plain array or an `{items, total}` object shape.
- Storyboard workflow now favors tile-first navigation:
  - single-click selects
  - double-click opens full-screen
  - each tile exposes an `Open spread` action
- macOS launchers were updated to route through the local project folder instead of stale external paths.
- Upload flow now includes inline status text in the layout drawer so failures are visible instead of silent.
- A checked-in requirements manifest now records the expected local runtime, models, and key shared paths.
- A repo-level doctor script now verifies Ollama availability, required models, and important writable directories.
- The Generate tab now shows a `Setup readiness` card fed by `/api/setup-status`, so model/path issues are visible inside the cockpit.
- The project picker now includes a `+ New project...` option, which opens a `Magic Book` flow for generated projects and optional overnight automation.
- The Manuscript tab now centers on `Manuscript` and `Dummy Layout` instead of exposing every manuscript file as a primary tab.
- `Dummy Layout` now has a `Sync to spreads` action so manuscript structure can refresh the downstream `Layout` and `Generate` tabs.
- `Spread prompts` were reframed as `Illustration planning`, with the editable image prompt shown up front and the semantic story fields tucked into a collapsed advanced section.
- The Magic Book modal now shows live progress in place, including a tiny inferred step tracker for source story, spread planning, and rendering.
- The Generate tab now exposes `Kill active run`, which aims to stop the active image-generation subprocess and block further retries in that workflow.

## Magic Book

The first-pass `Magic Book` flow is local-only and meant to be fun, fast, and recoverable.

How it works now:

- open the project picker and choose `+ New project...`
- give the project a title and paste a story seed or creative brief
- the app first writes a fuller source-story draft from that brief
- that generated story is saved into the project’s Manuscript source-material inbox
- the saved story is then used to build the manuscript, spread text, and image prompts
- leave `Overnight mode` on to continue directly into full-book spread rendering and recursive image review/retry
- turn `Overnight mode` off if you only want the generated story, project files, and prompts first
- the modal now includes a `Load tiny test` helper to drop in a small one-page-style story brief for end-to-end overnight testing

What it creates:

- a generated project under `projects/generated/`
- source-story files in the shared manuscript uploads area for that project
- manuscript files in that project’s `manuscript/` folder
- spread prompt files in `storyboard/prompts/`
- a custom project entry persisted in `data/dashboard-projects.json`
- spread imports into the main cockpit once planning finishes

First-pass implementation notes:

- custom projects are dynamic; they are not hard-coded into `DASHBOARD_PROJECTS`
- story drafting and spread planning each try a local Ollama text pass first and fall back if needed
- overnight rendering reuses the existing local recursive judge loop rather than a separate render path
- Generate-tab status now reports the overnight phases more explicitly: drafting source story, planning spreads, then rendering spread `n` of `N`
- the Magic Book modal mirrors that shared run status live, including a small step tracker inferred from the current status text
- the intended Magic Book path is now a single button press after filling the modal; no extra Manuscript step is required to kick off the chain
- the generated-project picker entry can appear before planning is fully finished, so the safest flow is to wait for the status to settle before switching into the new project

Current limitation:

- this first pass is optimized for the existing Daniel-book production flow and copies the current Daniel reference anchor into generated projects for review continuity
- it is meant for fun overnight drafts, not final production-ready book planning

## Setup Status Handoff

The current setup-status flow is intentionally simple:

- [`project-requirements.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/project-requirements.json) is the source of truth for required models and shared paths.
- [`dashboard.py`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/dashboard.py) reads that manifest and exposes `/api/setup-status`.
- [`cockpit/app.js`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/app.js) fetches `/api/setup-status` during startup and after model-list refreshes.
- [`cockpit/index.html`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/index.html) renders the card in the `Generate` tab.
- [`cockpit/style.css`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/style.css) styles the card.

What the card currently reports:

- required models from the manifest
- shared path/file availability
- whether the current process can write to required local folders
- the doctor command to run manually

Important implementation note:

- the dashboard endpoint does not shell out to the doctor script
- it reuses the same manifest and performs a lightweight in-process check so the UI stays responsive

If a later pass needs richer setup reporting, extend these in order:

1. update [`project-requirements.json`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/project-requirements.json) if the dependency set changes
2. update `get_setup_status()` in [`dashboard.py`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/dashboard.py) if new runtime checks are needed
3. update `renderSetupStatus()` in [`cockpit/app.js`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/app.js) if the UI should show more detail

## Magic Book Handoff

The `Magic Book` path currently lives in these pieces:

- project creation API: [`dashboard.py`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/dashboard.py)
  - `create_magic_book()`
  - `run_magic_book_pipeline()`
  - `generate_magic_book_plan()`
  - `write_magic_book_project()`
- custom project registry: [`dashboard.py`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/dashboard.py)
  - `load_custom_projects()`
  - `save_custom_projects()`
  - `all_dashboard_projects()`
- header/modal UI: [`cockpit/index.html`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/index.html) and [`cockpit/app.js`](/Users/sky/Documents/codex/personal/projects/ancestor-books/image-gen/cockpit/app.js)

If a later model needs to extend it, this is the safest order:

1. change the project/planning data shape in `dashboard.py`
2. update generated manuscript/prompt file writers
3. update the modal UI fields
4. only then change how overnight automation decides which spreads to render

## Known Focus Areas

Current work is centered on tightening the storyboard workflow:

- make spread review and full-screen editing feel faster
- keep generation results tightly tied to the selected spread
- improve upload and assignment feedback

If behavior seems wrong, check these first:

- the active launcher is the copy inside this folder, not an older app elsewhere
- the dashboard URL in `.dashboard-url` matches the running local server
- the selected spread in Layout and Generate is the same one you expect
- the `Setup readiness` card and the doctor script agree on what is missing
