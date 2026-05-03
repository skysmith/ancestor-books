# Ancestor Books

Workspace for family-history children's picture books and related production materials.

This repository should keep durable source material, manuscripts, prompts, production scripts, and project notes in Git. Generated artwork, proof PDFs, KDP uploads, app bundles, temporary exports, and raw research exports should stay local.

## Workspace Metadata

- Name: Ancestor Books
- Domain: personal
- Status: active
- Purpose: Family-history children's books and the surrounding writing, research, and production workflow
- Path: personal/projects/ancestor-books
- Related:
  - personal/projects
  - personal/data
  - lab/media
  - lab/ai-art
- Tags:
  - books
  - family-history
  - publishing
  - illustration

## Current Focus

- `projects/daniel-cook-three-stories/` - combined Daniel Cook picture-book dummy built around three Revolutionary War family stories.
- `projects/generated/sieger-rides-through-the-snow/` - generated source package and notes for the Sieger Springer winter story.
- `projects/generated/the-cold-room-at-leek/` - generated source package and notes for the Leek room-warming story.

## Local-Only Assets

Generated and export-heavy material is intentionally ignored:

- artwork and image renders
- contact sheets and proof PDFs
- KDP cover/interior exports
- `output/`, `tmp/`, and archived dashboard payloads
- raw FamilySearch exports and local OAuth/token state

Keep polished story facts, manuscript text, source outlines, and production decisions in Markdown or scripts so they remain reviewable without committing art files.

## Standard Book Folder Shape

Each durable book project should prefer this shape:

- `README.md` for current status and project scope
- `manuscript/` for manuscript, dummy layout, and source outline
- `notes/` for editorial and production notes
- `art/briefs/` for reusable visual direction
- `storyboard/prompts/` for image prompts when a dummy is ready for visual work
- `production/` for build scripts and print/export workflow notes

Generated art belongs outside Git even when it lives inside the project folder.
