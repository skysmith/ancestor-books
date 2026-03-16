# Ancestor Books

Workspace for family-history children's picture books and related production materials.

## Publishing Target

Default publication target is Amazon KDP paperback. See [`KDP.md`](./KDP.md) for the repo-wide publishing checklist and file-prep rules.

## Research Integrations

- [`FAMILYSEARCH.md`](./FAMILYSEARCH.md) documents the local FamilySearch research flow for ancestor-story sourcing.
- `scripts/familysearch_story_research.py` is the local CLI for FamilySearch OAuth, tree reads, and story-dossier export.

## Image Generation Dashboard

- The image-generation workflow now lives entirely inside this repo at `image-gen/` so the observation pipeline moves with the stories.
- Launch the dashboard from `personal/projects/ancestor-books/image-gen/Image Gen Dashboard.app` or run `personal/projects/ancestor-books/image-gen/launch_dashboard.sh` to start `dashboard.py` in this folder.
- Any past references to `/lab/media/image-gen` should now resolve to `personal/projects/ancestor-books/image-gen/outputs/prompts/<timestamp>` (the timestamps in `outputs/prompts/` are linked to each generation folder, and `outputs/images/` mirrors all generated images for quick previews).
- Generated runs keep their `prompt.txt`, `negative_prompt.txt`, `settings.json`, and logs inside `image-gen/outputs/prompts/<timestamp>/`, and each generation’s image is copied into `image-gen/outputs/images/` for browsing without opening every run folder.
- Each timestamped bundle also writes `metadata.json` and `images.json` so it can describe the settings and map directly from image names back to the mirror path.

> Legacy `/lab/media/image-gen` is retired; treat `personal/projects/ancestor-books/image-gen/outputs/...` as the active workspace and update any references accordingly.

## Repository Map

This repository is organized as one folder per mainline book inside `projects/`.

- `projects/01-captain-daniel-and-the-night-of-courage/` active book 1 package with manuscript, storyboard, exports, and production files
- `projects/02-the-hungry-winter/` active book 2 package with manuscript, storyboard, outputs, and production files
- `projects/03-the-watchful-dog/` active book 3 package
- `projects/04-the-torys-honey/` active book 4 package using the strongest current honey-story build

Archived or alternate versions live in `archive/` when a folder is no longer part of the mainline sequence.

## Standard Book Folder Shape

Each project should follow the same baseline structure, even if some folders stay sparse until later:

- `README.md` short status, current scope, and next steps
- `manuscript/manuscript.md` current working manuscript
- `manuscript/dummy-layout.md` page-by-page or spread-by-spread layout draft
- `manuscript/source-outline.md` extracted source material, quotes, chronology, or outline notes when available
- `notes/project-brief.md` editorial intent, audience, and project constraints
- `art/briefs/illustration-brief.md` visual direction for the book
- `art/briefs/storyboard-production-checklist.md` production checklist for storyboard and image generation stages
- `art/briefs/thumbnail-sheet.md` spread-by-spread thumbnail and composition notes
- `art/references/` visual reference material when needed
- `storyboard/prompts/` spread prompts for image generation when the book reaches storyboard phase
- `storyboard/frames/` rough storyboard board images
- `storyboard/renders/inbox/` incoming image generations for review
- `storyboard/renders/raw/` work-in-progress renders, review artifacts, and candidate images
- `storyboard/renders/selects/` chosen renders that are treated as approved selections
- `outputs/` compiled contact sheets, rough dummy PDFs, and presentation exports
- `production/production-notes.md` print, sequencing, and handoff notes
- `production/kdp-checklist.md` per-book publication checklist copied from `templates/kdp-checklist.template.md`
- `production/end-to-end-plan.md` project pipeline notes when the book is far enough along to need them
- `scripts/` one-off helpers used by that specific book

Not every book will need every folder immediately, but new books should start from the same contract.

Current dashboard convention:

- `raw/` images can appear in the Layout tab as `Candidate` previews when a spread has no selected image yet.
- A spread becomes truly approved when its chosen image is promoted into `storyboard/renders/selects/`.

## How To Add A New Book

When creating book 6 or any later project, use this sequence:

1. Create `projects/<slug>/` using a lowercase hyphenated slug.
2. Add a project `README.md` with working title, status, structure summary, and next steps.
3. Create `manuscript/`, `notes/`, `art/briefs/`, and `production/` immediately.
4. Add these baseline files:
   - `manuscript/manuscript.md`
   - `manuscript/dummy-layout.md`
   - `notes/project-brief.md`
   - `art/briefs/illustration-brief.md`
   - `production/production-notes.md`
   - `production/kdp-checklist.md` copied from `templates/kdp-checklist.template.md`
5. Add `manuscript/source-outline.md` as soon as source text, quotes, or chronology has been gathered.
6. Add storyboard folders only when the manuscript is stable enough for visual sequencing:
   - `storyboard/prompts/`
   - `storyboard/frames/`
   - `storyboard/renders/inbox/`
   - `storyboard/renders/selects/`
   - `outputs/`
7. Update this top-level `README.md` so the repository map and series plan stay current.

## New Book Starter Checklist

Use this checklist for future project creation:

- Choose canonical title and slug.
- Record the source passage or ancestor story before rewriting it.
- Draft `project-brief.md` with target age, tone, and historical constraints.
- Create the working manuscript in `manuscript/manuscript.md`.
- Build the first dummy layout in `manuscript/dummy-layout.md`.
- Write or expand the illustration brief once the emotional beats are stable.
- Only start storyboard prompt generation after the dummy layout is coherent.
- Export contact sheets and rough dummies into `outputs/` rather than scattering them elsewhere.
- Copy `templates/kdp-checklist.template.md` into the new project's `production/` folder early so publication requirements stay visible.
- Keep one project per ancestor story; avoid mixing multiple books in one folder.
- Keep raw FamilySearch exports local and distill only the relevant story material into `manuscript/source-outline.md`.

## Series Plan

1. Night of Courage
2. The Hungry Winter
3. The Watchful Dog
4. The Tory's Honey

## Archive

- `archive/04-the-torys-honey-split-version/` older split camp-search version preserved during folder cleanup

## Editorial Note

The current `04-the-torys-honey` folder contains the strongest combined honey-story build. That means there is still some narrative overlap with `03-the-watchful-dog`.

If you later want the cleanest non-overlapping series, choose one of these paths:

- keep `03-the-watchful-dog` and revise `04-the-torys-honey` back to the camp-search-only version
- or keep the combined `04-the-torys-honey` and retire `03-the-watchful-dog`
