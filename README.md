# Ancestor Books

Workspace for family-history children's picture books and related production materials.

## Publishing Target

Default publication target is Amazon KDP paperback. See [`KDP.md`](./KDP.md) for the repo-wide publishing checklist and file-prep rules.

## Repository Map

This repository is organized as one folder per book inside `projects/`.

- `projects/captain-daniel-and-the-night-of-courage/` active book 1 package with manuscript, storyboard, exports, and production files
- `projects/the-hungry-winter/` active book 2 package with manuscript, storyboard, outputs, and production files
- `projects/the-honey-barrel-trick/` active book 3 package with manuscript, art brief, and production notes
- `projects/the-watchful-dog/` active book 4 package with manuscript, art brief, and production notes
- `projects/the-torys-honey/` active book 5 package with manuscript, art brief, and production notes

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
- `storyboard/renders/selects/` chosen renders
- `outputs/` compiled contact sheets, rough dummy PDFs, and presentation exports
- `production/production-notes.md` print, sequencing, and handoff notes
- `production/kdp-checklist.md` per-book publication checklist copied from `templates/kdp-checklist.template.md`
- `production/end-to-end-plan.md` project pipeline notes when the book is far enough along to need them
- `scripts/` one-off helpers used by that specific book

Not every book will need every folder immediately, but new books should start from the same contract.

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

## Series Plan

1. Night of Courage
2. The Hungry Winter
3. The Honey Barrel Trick
4. The Watchful Dog
5. The Tory's Honey
