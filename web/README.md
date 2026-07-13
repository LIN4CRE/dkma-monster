# DKMA Monster — Web dashboard

A self-hostable, searchable keep-alive guide (like dontkillmyapp.com) that is
**generated entirely from `data/oem_registry.json`** — the same source the CLI,
desktop GUI, root script, Magisk module and in-app library use. Edit the registry
once and every layer, including this site, stays in sync.

> 👀 **View it now:** open `web/site/index.html`. Search your brand, click through
> to per-OEM step-by-step instructions. Fully static — inline CSS/JS, no external
> resources, so it renders in the in-app viewer and offline.

## Build

```bash
python3 web/build.py            # writes the site into web/site/
python3 web/build.py --out DIR  # custom output directory
```

Output:
```
web/site/
├── index.html          # searchable brand grid + "big three" + automation CTA
└── oem/
    ├── xiaomi.html      # one page per OEM family (15 total)
    ├── samsung.html
    └── …
```

## Serve it (optional)

Any static host works. To preview locally:
```bash
python3 -m http.server -d web/site 8080   # → http://localhost:8080
```
Or drop `web/site/` on GitHub Pages, Netlify, S3, nginx — no backend needed.

## How the content is produced

- **Technical data** (component names, intents, matching) comes from the registry.
- **User-facing wording** (plain-English step titles + "why") lives in
  `STEP_GUIDE` inside `build.py`, keyed by step `id`. Add a new step id there to
  give it friendly copy; unknown ids fall back to the registry title.
- Each brand page also has a **Developer** disclosure showing the exact settings
  Activities the tools open, so it's useful to both end users and integrators.

## Regenerating after registry edits
Whenever you add an OEM or fix a component in `data/oem_registry.json`
(see `docs/CONTRIBUTING.md`), just re-run `python3 web/build.py`. Consider wiring
this into CI so the published site tracks the registry automatically.
