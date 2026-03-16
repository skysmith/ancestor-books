# Image Gen Workflow

1. Launch `launch_dashboard.sh` from `/personal/projects/ancestor-books/image-gen` so the server writes into `outputs/prompts/<timestamp>/` and the `outputs/images/` mirror.
2. Input your prompt, size, steps, and optional review settings; the dashboard saves `prompt.txt`, `negative_prompt.txt`, `settings.json`, `metadata.json`, and `images.json` inside the timestamped folder.
3. Run the built-in Review / Adjust flows to produce `review.scorecard.*` files inside the same folder.
4. When you want to include an image in a book, grab it either from the run folder or from `outputs/images/` (the metadata and `images.json` entries point back to the mirror path).
5. Keep `/lab/media/image-gen` as a read-only archive; all new runs stay under ancestor-books.
