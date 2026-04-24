# Sieger Spread Audit v2

## Goal

Convert the book back to a true spread-based interior:

- design as `12` full spreads
- split each spread into `24` single pages for KDP

## Pre-Split Checklist

- Each spread must exist as a real horizontal source image, not a screenshot of a square page.
- Preferred source ratio is `2:1` horizontal before splitting.
- No important face, hand, bicycle wheel, or text block should sit directly on the center fold.
- Text should live clearly on one side of the spread, with safe margin from trim.
- Each spread should be available at print-usable resolution, not browser-capture resolution.
- Final page sequence must be complete from page `1` through page `24`.

## What Exists Locally Right Now

### Sieger Rides Through the Snow

Available source spreads:

- `spread-01-news-setting-out.png`
- `spread-02-wind-against-him.png`
- `spread-03-zwolle-search.png`
- `spread-04-train-turn.png`
- `spread-05-arnhem-service.png`
- `spread-06-return-ride.png`
- `spread-07-love-keeps-going.png`

Source folder:

- `/Users/sky/Documents/codex/personal/projects/ancestor-books/projects/generated/sieger-rides-through-the-snow/renders/chatgpt-round1/`

Important limitation:

- these are first-pass ChatGPT browser captures
- current local size is only `480 x 320` each
- this is useful for draft slicing and sequencing only
- this is not sufficient for print export

### The Cold Room at Leek

Available local art is incomplete:

- only first-pass partial renders exist for spread `1` and spread `2`
- spreads `3-7` are not present locally as finished spread art
- pages `8-14` currently survive mainly as text overlays and Canva state, not full print assets

Relevant folder:

- `/Users/sky/Documents/codex/personal/projects/ancestor-books/projects/generated/the-cold-room-at-leek/`

## Audit Result

Current status: `draft-only`

What is safe to do now:

- slice the available `7` Sieger spreads into single-page draft halves
- confirm the page ordering and gutter logic
- keep the slicing workflow ready for the full `12`-spread book

What is not safe to do yet:

- build the final KDP interior from current local assets
- send the current sliced files to print

## Next Requirement For Final KDP Interior

One of these has to happen before the true `24`-page proof interior can be finalized:

1. Export the full `12` laid-out spreads from Canva at proper resolution.
2. Save the finished spread assets locally for both stories.
3. Then run the spread slicer on those real spread exports.

## Draft Slice Output

Draft slicing should go to:

- `/Users/sky/Documents/codex/personal/projects/ancestor-books/projects/generated/sieger-rides-through-the-snow/renders/chatgpt-round1/sliced-draft-pages/`

This output is for sequencing and production verification, not print.
