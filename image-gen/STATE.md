# Image Gen Dashboard State

Updated: 2026-03-15

## Summary

The local `Image Gen Dashboard` has moved from a rough demo into a usable spread-based cockpit tied to the real `ancestor-books` workspace.

Current default working project:

- `Book 2: The Hungry Winter`

Current print target assumption:

- Amazon KDP paperback
- full bleed
- `8.5" x 8.5"` square picture book

## What Works Now

### Launch and local runtime

- The dashboard launches from the local project folder instead of stale external paths.
- The packaged app, `.command` launcher, and shell launcher all point into this repo.
- The dashboard writes the active local URL into `.dashboard-url`.
- The local packaging direction is now explicit: models are dependencies, not API integrations.
- Required runtime/models are recorded in `image-gen/project-requirements.json`.
- Setup can be checked with `scripts/check_image_gen_setup.py`.
- The Generate tab now surfaces a lightweight in-app `Setup readiness` card.
- The project picker now exposes a `+ New project...` flow for generated `Magic Book` projects.

### Cockpit structure

- The UI is now centered on four tabs:
  - `Layout`
  - `Generate`
  - `Assets`
  - `Manuscript`
- Storyboard tiles select a spread and open a detail drawer.
- `Open spread` opens the fullscreen spread view.
- Tile cards now have larger thumbnail previews instead of ultra-thin image strips.

### Storyboard and spread preview

- Full-spread (`span`) art renders as one continuous spread in fullscreen.
- The seam is visually joined with a center gutter line.
- Page labels appear above the fullscreen artwork.
- The right-page label is right-aligned.

### Text overlay

- Text overlay can be positioned and saved per spread.
- For `span` spreads, fullscreen uses one shared footer-style overlay instead of duplicated left/right text boxes.
- The current default overlay placement is intentionally conservative for KDP full-bleed interior work.

### Real project loading

- The dashboard can now import from real book folders instead of only using demo data.
- Project discovery is currently wired for:
  - `Book 1: Night of Courage`
  - `Book 2: The Hungry Winter`
- The active implementation starts with `Book 2`, because it has the cleanest prompt/render structure.
- Imported data pulls from:
  - `manuscript/dummy-layout.md`
  - `storyboard/prompts/`
  - `storyboard/renders/selects/`

### Book 2 import

- `Book 2` spreads are now represented in the dashboard data model.
- Selected renders from the Book 2 storyboard folder are used as assigned spread art when available.
- Spread prompt text is sourced from the real prompt sheets and selected render metadata.

### Assets and uploads

- Drag/drop and button uploads now assign back to the selected spread.
- Upload status is surfaced inline in the layout drawer.
- Uploaded art can display in spread preview and fullscreen.

### Manuscript organization

- The Manuscript tab can read uploaded source documents from `data/manuscript-sources/`.
- It now centers the `Book text` column on:
  - `Manuscript`
  - `Dummy Layout`
- Manuscript files can now be edited inline from the dashboard while staying locked by default.
- `Dummy Layout` is now the explicit bridge into `Layout` and `Generate`.
- A `Sync to spreads` action re-imports the current project from `dummy-layout.md`.
- The middle column is now framed as `Illustration planning` rather than generic prompt review.
- Each spread card now shows:
  - spread text
  - editable image prompt
  - collapsed advanced story-planning fields
- Each spread card also has a `Lock planning` control so illustration-planning edits can be frozen per spread.

### Magic Book generation

- A first-pass `Magic Book` flow can now create generated projects from a pasted story seed or creative brief.
- Generated projects are persisted through `data/dashboard-projects.json` instead of being hard-coded.
- The flow now drafts a fuller source story first, saves that into the project’s manuscript source-material area, then plans the book from that saved story.
- Overnight mode plans the book, writes manuscript/prompt files, imports the project, and then runs the existing recursive spread-generation loop sequentially.
- Story drafting and spread planning each prefer a local Ollama text pass and fall back when unavailable.
- The product intent for `Magic Book` is now explicitly one-button: brief -> source story -> manuscript/spreads/prompts -> overnight rendering loop.
- The modal includes a built-in `Load tiny test` helper for a small end-to-end overnight verification run.
- The modal now shows live progress for the current run, so users do not have to switch over to Generate just to see whether Magic Book is moving.

### Reference cues

- `image-gen/inbox/` is now treated as a lightweight reference-image inbox.
- Current inbox files include:
  - `daniel sitting.png`
  - `image 2.png`
- A spread can now store:
  - `reference_notes`
  - `reference_images`
- Reference images can be attached/detached per spread in the drawer UI.
- Reference notes are appended into the effective generation prompt and stored in run metadata.

## Important Constraint

Reference images are not yet true multimodal conditioning.

What is implemented now:

- spread-level storage of reference images
- visual reference management in the cockpit
- reference notes appended into the prompt
- reference metadata saved into generation runs

What is not implemented yet:

- passing the attached images directly into a multimodal image generation model
- enforcing face lock/style lock from the image files themselves at generation time

So today the reference system is a strong workflow/organization layer, but still prompt-driven under the hood.

## Known Issues

### Fullscreen overlay toggle

- `Toggle text overlay` is still unreliable.
- It can turn the overlay off, but restoring/re-toggling behavior is inconsistent.
- Dragging the overlay also appears to become unreliable after the first move.
- This feature may be worth simplifying or temporarily removing if it slows down review.

### Overlay editing UX

- Footer placement is closer to a real picture-book layout now, but it still needs a clearer “safe area” editing model.
- We do not yet show explicit KDP-safe guides in the UI.

### Project switching verification

- The backend project loader and selector are implemented, but the live browser behavior still needs a clean manual verification pass after restart.

### Packaging follow-through

- The first-pass packaging artifacts are now in place and the dashboard surfaces model/path readiness in the Generate tab.
- The UI card is backed by `/api/setup-status` in `dashboard.py`, not by directly running the doctor script.
- The command-line doctor script is still the deeper manual verification path.

### Setup status handoff

- `project-requirements.json` is the dependency source of truth.
- `dashboard.py:get_setup_status()` reads that manifest and emits `/api/setup-status`.
- `cockpit/app.js:refreshSetupStatus()` and `renderSetupStatus()` populate the Generate-tab card.
- The card refreshes on startup and after the Ollama model list is refreshed.
- If later work adds more dependencies, update the manifest first, then the backend summary, then the UI rendering.

### Magic Book handoff

- `dashboard.py:create_magic_book()` starts the generated-project flow.
- `dashboard.py:run_magic_book_pipeline()` is the background worker for planning plus optional overnight rendering.
- `dashboard.py:generate_magic_book_story()` turns the short brief into a fuller source-story draft before spread planning.
- `dashboard.py:generate_magic_book_plan()` is the local planner entry point.
- `dashboard.py:save_manuscript_text_source()` writes the generated source story into the Manuscript source-material area for the new project.
- `dashboard.py:write_magic_book_project()` writes the generated manuscript and prompt files.
- `cockpit/index.html` and `cockpit/app.js` provide the header modal entry point.
- The Magic Book modal now includes a live progress panel driven by the shared `/api/status` poll. It will show `Busy` when some non-Magic-Book generation job is already occupying the global run slot.
- The modal now also renders a tiny inferred step list (`source story`, `spread plan`, `render book`) by parsing the status text rather than reading a separate backend progress payload.
- `data/dashboard-projects.json` is the custom-project registry that feeds the project picker.

### Manuscript prompt-card handoff

- `cockpit/style.css` now keeps spread text in the prompt cards smaller and quieter so it reads like supporting manuscript copy rather than a headline.
- `cockpit/app.js:renderPromptCards()` is where the visible ordering of spread text, image prompt, lock button, and advanced planning fields is controlled.

### Manuscript handoff

- `dashboard.py:import_dashboard_project()` still rebuilds spread records from `manuscript/dummy-layout.md`.
- `cockpit/app.js` now exposes that import step as `Sync to spreads` inside the `Dummy Layout` document viewer.
- `Layout` and `Generate` still work from the imported spread records, not directly from `manuscript.md`.
- If later work adds a truer editorial pipeline, `manuscript.md` and `dummy-layout.md` should either stay synchronized automatically or show their relationship more explicitly in the UI.

### Layout semantics

- `left`, `right`, `span`, and `inset` are stored and displayed, but image assignment is still basically one-asset-per-spread.
- We do not yet support:
  - separate left-page and right-page image assets
  - true one-side-only rendering logic in layout mode
  - automatic split/blank behaviors for left-only or right-only images

## KDP Layout Assumptions

Current overlay/footer decisions assume:

- `8.5" x 8.5"` trim
- full bleed
- standard KDP paperback safety guidance

Working safety target being used in the UI:

- keep text clear of trim and bleed edges
- avoid placing text into the gutter
- prefer a low centered footer band for full-spread story copy

This is conservative rather than mathematically exact. A future pass should add visible safe guides based on trim, bleed, and gutter assumptions.

## Recommended Next Steps

### Highest-value next

1. Verify the Manuscript tab and project switching live after a full dashboard refresh.
2. Decide whether to keep or temporarily remove the fullscreen overlay toggle/drag interaction.
3. Add visible KDP-safe guides to fullscreen spread view.
4. Decide whether `Dummy Layout` sync should stay manual or become the default after save.

### Next workflow gains

1. Make the `Magic Book` planner smarter about true picture-book pacing and front matter instead of always targeting a simple 10-spread draft.
2. Make left-page and right-page layouts render distinctly instead of behaving like span-by-default with different metadata.
3. Show attached reference cues inside the `Generate` tab as well, not only in the layout drawer.

### Later / deeper

1. Add true multimodal reference-image conditioning if the generation stack supports it.
2. Add a persistent project import/cache layer rather than repopulating from book folders ad hoc.
3. Add export/debug views for print-safe spread proofs.

## Bottom Line

This is now a real working storyboard cockpit, not just a prototype shell.

The strongest current state is:

- `Book 2` loaded into the dashboard
- local runtime/model expectations documented and checkable
- setup readiness visible inside the cockpit, not only in terminal docs
- full-spread preview behaving more like a real picture-book spread
- KDP-oriented bottom footer text treatment
- real uploads, selected renders, and reference cues all attached to spreads
- manuscript editing and spread sync now have a clearer separation of roles:
  - `Manuscript` for story draft
  - `Dummy Layout` for spread structure consumed by the rest of the cockpit

The main rough edge left in the interaction model is text overlay editing in fullscreen.
