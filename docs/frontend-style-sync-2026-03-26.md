# Frontend Style Sync Note (2026-03-26)

## What I changed
This pass ported the flatter, more modern cockpit styling from the `ai-art` dashboard into the Ancestor Books dashboard.

Updated file:
- `image-gen/cockpit/style.css`

The visual changes include:
- lighter dashboard surfaces and cleaner card borders
- flatter tabs, buttons, and form controls
- more consistent spacing, radii, and panel treatment
- updated layout-grid tile styling and drawer styling
- cleaner generation, assets, and manuscript card presentation

I also preserved the Ancestor Books-specific `.field-static` class after syncing the shared stylesheet so the local UI keeps its extra field treatment.

## Important repo state
This repository already had many unrelated uncommitted changes before this pass.

Inside `image-gen/cockpit/`, these files were already dirty when I started:
- `image-gen/cockpit/app.js`
- `image-gen/cockpit/index.html`
- `image-gen/cockpit/style.css`

From my work in that directory, I only changed:
- `image-gen/cockpit/style.css`

I did not make new edits to:
- `image-gen/cockpit/app.js`
- `image-gen/cockpit/index.html`

## What to commit
If you want to commit only the style-port work from this pass, the safest set is:
- `image-gen/cockpit/style.css`
- `docs/frontend-style-sync-2026-03-26.md`

If you are preparing a larger cockpit/frontend commit, review the already-existing changes in:
- `image-gen/cockpit/app.js`
- `image-gen/cockpit/index.html`
- `image-gen/cockpit/style.css`

## Suggested commit split
Option 1: isolated style sync
- stage `image-gen/cockpit/style.css`
- stage `docs/frontend-style-sync-2026-03-26.md`

Option 2: broader cockpit update
- review and stage the cockpit HTML/JS changes separately if they belong with the visual refresh

## Verification note
I did not run the full Ancestor Books dashboard against its backend after this sync. The port was done because the cockpit structure matches the `ai-art` dashboard closely, and the stylesheet was transferred onto the same UI shell.
