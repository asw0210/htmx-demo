# htmx-demo
FastAPI + HTMX teaching app. Each card on the home page demonstrates one HTMX feature with a server-rendered fragment so you can inspect the request/response cycle.

## Run
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

On Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

If you are using `uv`:
```bash
uv pip install -r requirements.txt
uvicorn main:app --reload
```

## What To Look For
- `hx-get` + `hx-target` for fragment replacement
- `hx-post` for form submissions
- `hx-trigger` for debounced search and polling
- `hx-swap` strategies (`innerHTML`, `outerHTML`, `beforeend`)
- `hx-swap-oob` for out-of-band updates
- `hx-push-url` for fragment navigation
- `hx-boost` for enhanced link navigation
- `hx-indicator` for loading states
- `hx-include`, `hx-vals`, `hx-headers` for request shaping
- `hx-delete`, `hx-put`, `hx-confirm` for REST-ish actions
- `hx-select` for selecting a subset of response HTML
- `hx-sync` to cancel in-flight requests
- `hx-params` to filter submitted parameters
- `hx-preserve` to keep local state across swaps
- `hx-disabled-elt` to disable elements while requests run
- `HX-Redirect` response header for client redirects
- `hx-patch`, `hx-validate`, `hx-encoding`, `hx-request`, `hx-prompt`
- `hx-select-oob`, `hx-replace-url`, `hx-disable`, `hx-disinherit`, `hx-inherit`
- `hx-history`, `hx-history-elt` for history cache control
- `hx-on` for inline events
- Swap lifecycle classes (`htmx-added`, `htmx-swapping`, `htmx-settling`)
- Response headers: `HX-Push-Url`, `HX-Replace-Url`, `HX-Location`, `HX-Refresh`,
  `HX-Reswap`, `HX-Retarget`, `HX-Reselect`, `HX-Trigger`,
  `HX-Trigger-After-Swap`, `HX-Trigger-After-Settle`
- JS API: `htmx.ajax`, `htmx.trigger`, and runtime `htmx.config`
- Extensions: `head-support`, `preload`, `response-targets`, `sse`, `ws`, `morph`

## Notes
- All HTML is server-rendered, so the app remains functional without HTMX.
- Use your browser devtools to inspect the request headers and the swapped HTML fragments.

## Jinja + HTMX
This app uses Jinja templates to render both full pages and partial fragments that HTMX swaps into the DOM.
Check the “Jinja + HTMX” card on the home page:
- The server renders `templates/partials/jinja_demo.html` with variables and loops.
- HTMX injects that HTML into the target without a full page refresh.
Check the “Jinja macros + reuse” card:
- The fragment imports `templates/partials/_macros.html`.
- Shared macro output is swapped in by HTMX.
Check the “Jinja inheritance” card:
- The fragment extends `templates/partials/_fragment_base.html`.
- Blocks are overridden and swapped in like any other HTMX response.

## Using This As A Guide
This app is intentionally structured in three layers:
- Feature catalog: cards list the available HTMX features.
- Interactive playground: each card is clickable so you can observe the request/response behavior.
- Implementation guide: the “Feature Guide” section includes minimal HTML snippets to copy into your app.
The home page also includes a Feature Index sidebar for quick navigation.
Each demo card includes tags for faster scanning, and there is a back-to-top button.
The Feature Index includes a filter input to quickly find a demo.
The filter supports a clear button and highlights matched text.
There is a grid filter for the demo cards, copy buttons for the feature guide snippets,
per-card “How to implement” toggles, and a swap strategy sandbox for side-by-side comparison.
The “How to implement” panels now include both the HTML snippet and a matching FastAPI route stub.
Those route stubs are derived from the actual handlers in `main.py` at runtime.
Each panel also includes a toggle to reveal the full handler source.
Every demo card includes links to the official documentation for that feature.
The Feature Guide now includes a "Problem solved" line for each item.

## Async Dashboard (Worker Simulation)
The async dashboard demonstrates how to append tiles to a page as background workers complete.
It simulates five workers that each sleep 10–90 seconds and then publish a tile.

How it works:
1. `GET /page/async-dashboard` creates a new `run_id` and starts five background tasks.
2. The page renders an empty `#async-tiles` container and a polling element.
3. The browser polls `GET /async-dashboard/poll?run_id=...` every second.
4. The server returns only new tiles since the last `offset`.
5. HTMX appends those tiles with `hx-swap="beforeend"` and updates the `offset` via OOB swap.
6. When all workers are done, the poller is replaced with “All workers finished.”

Key HTMX features used:
- `hx-trigger="every 1s"` for polling
- `hx-swap="beforeend"` for incremental append
- `hx-swap-oob` to update hidden state and stop polling
