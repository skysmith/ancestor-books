# KDP Paperback Guide

This repository targets Amazon KDP paperback output for children's picture books.

Use this guide when preparing any `ancestor-books` project for publication.

## Default Publishing Assumption

Unless a project says otherwise, prepare the book for:

- Amazon KDP paperback
- full-bleed interior
- Canva or equivalent layout tool for interior assembly
- PDF export for both interior and cover

## Core KDP Requirements

These are the practical requirements to keep every project publishable on KDP:

- Interior file must be a print-ready `PDF`.
- Interior must be uploaded as single pages, not reader spreads.
- Full-bleed books need `0.125"` bleed on top, bottom, and outer edge.
- Images should be `300 DPI`.
- Fonts should be embedded in exported PDFs.
- Interior and cover files should not include crop marks, trim marks, comments, or watermarks.
- Paperback page count must be at least `24` pages.
- Final page count should be even.
- Cover file must be a single full-wrap PDF containing back cover, spine, and front cover.
- Final cover dimensions must come from the KDP cover calculator after trim size, paper, ink, and page count are locked.
- Spine text is only available when the book is over `79` pages.

## Project Metadata To Lock Early

Each book should record these decisions before final export:

- trim size
- bleed or no-bleed
- target page count
- paper type
- ink type
- whether the spine will carry text
- target publication owner / KDP account

Record these in the book's `production/production-notes.md`.

## Recommended Repo Workflow

For each book:

1. Draft and revise story text in `manuscript/manuscript.md`.
2. Build page flow in `manuscript/dummy-layout.md`.
3. Confirm the intended trim size before final art placement.
4. Keep illustration outputs high resolution enough for `300 DPI` placement at final print size.
5. Assemble the print interior in Canva or another layout tool using single-page layout.
6. Export the interior as print PDF.
7. Generate the exact KDP cover template using the final page count and print specs.
8. Build the cover on that template and export as print PDF.
9. Run KDP preview checks before submission.

## Canva Notes

Canva is acceptable for this workflow if the export is controlled carefully:

- Create the document at the final trim size, with bleed enabled if Canva supports it for the chosen format.
- Keep all important text and faces inside safe margins.
- Export as PDF for print.
- Verify no page spreads were introduced in export.
- Verify raster art remains sharp at print size.

## Preflight Checklist

Before uploading to KDP, confirm:

- Manuscript is final and page count is locked.
- Interior is exported as single-page PDF.
- All full-bleed pages extend past trim.
- No critical text or faces sit too close to trim or gutter.
- All images remain crisp at final size.
- Front matter and end matter are in the final page count.
- ISBN / imprint decisions are settled if applicable.
- Cover template matches the exact final page count.
- Barcode area on the back cover is unobstructed.
- KDP previewer reports no blocking errors.

## Suggested Per-Book Additions

To keep each project publication-ready, each book should eventually include:

- print specs in `production/production-notes.md`
- a per-book checklist at `production/kdp-checklist.md`
- final export filenames in `outputs/`
- a short publication checklist in `production/`
- notes on what was done in Canva, if Canva was used

Start from `templates/kdp-checklist.template.md` when creating the per-book checklist.

## Sources

- [KDP Paperback Submission Guidelines](https://kdp.amazon.com/en_US/help/topic/G201857950)
- [KDP Save Your Manuscript File](https://kdp.amazon.com/en_US/help/topic/G202145060)
- [KDP Trim Size, Bleed, and Margins](https://kdp.amazon.com/help/topic/GVBQ3CMEQW3W2VL6)
- [KDP Cover Calculator](https://kdp.amazon.com/cover-calculator)
