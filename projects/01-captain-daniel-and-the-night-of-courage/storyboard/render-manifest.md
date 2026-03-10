# Render Manifest

## Purpose

Track incoming generated images and assign them cleanly to spreads during the rough-book assembly pass.

## Inbox

- `storyboard/renders/inbox/` for fresh incoming images from OpenClaw

## Promote Path

1. Review incoming files in `inbox/`
2. Move useful raw outputs to `raw/`
3. Promote strongest options to `selects/`
4. Replace or supplement `frames/` with selected rough art when approved

## Naming Convention

- `spread-01-v001.png`
- `spread-01-v002.png`
- `spread-04-v001.png`
- `spread-07-v003.png`

If multiple composition variants are useful:

- `spread-07-a-v001.png`
- `spread-07-b-v001.png`

## Anchor Spread Priorities

Start by filling these first:

1. `spread-01`
2. `spread-02`
3. `spread-04`
4. `spread-07`
5. `spread-10`
6. `spread-14`

## Selection Criteria

- Daniel reads young and consistent with the art brief
- The wall feels tall and dangerous in the climb spreads
- Blood remains restrained in aftermath scenes
- Text-safe space exists where planned
- Lighting matches the intended spread mood

## Replace Strategy

The current `storyboard/frames/*.png` files are rough planning boards. As generated images arrive:

- keep the boards as layout references
- place selected image renders in `storyboard/renders/selects/`
- later create a second assembled dummy that swaps selected renders into the board sequence
