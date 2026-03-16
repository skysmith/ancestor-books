# Image Gen Decisions

- **Outputs split**: The dashboard now writes timestamped run bundles under `outputs/prompts/<timestamp>/` and mirrors every generated PNG/JPG into `outputs/images/`. This keeps metadata and art separate while keeping a simple mirror for quick browsing.
- **Metadata plus linkage**: Each run folder gets `metadata.json` and `images.json` so scripts and people can trace an image back to its run and vice versa.
- **Legacy paths**: `/lab/media/image-gen` continues to exist for past work, but it is deprecated; new work lives entirely inside `personal/projects/ancestor-books/image-gen`.
- **Approved vs. experimental**: When we need a canonical archive of approved scenes (versus the full experimental output), add an `outputs/approved/` (or `references/approved_images.md`) layer so each image’s provenance is explicit.
- **Future rename**: The `outputs/prompts/` name is intentionally descriptive of run bundles, but once we confirm there are no harmful side effects we should rename it to `outputs/runs/` so the folder name matches its content.
