from __future__ import annotations

import asyncio
import inspect
import json
import random
import time
import uuid
from datetime import datetime
from threading import Lock
from time import sleep
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="HTMX Teaching App", version="1.0.0")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def render(request: Request, template_name: str, **context: Any) -> HTMLResponse:
    return templates.TemplateResponse(
        template_name,
        {"request": request, **context},
    )


counter_lock = Lock()
counter_value = 0
animate_lock = Lock()
animate_value = 0
morph_lock = Lock()
morph_flip = False

todos_lock = Lock()
todos = [
    {"id": 1, "text": "Skim the HTMX docs", "done": False},
    {"id": 2, "text": "Wire a form with hx-post", "done": False},
    {"id": 3, "text": "Try hx-swap-oob", "done": True},
]
next_todo_id = 4

catalog = [
    "Alpine JS",
    "Anchor Tag",
    "Async UI",
    "Boosted Links",
    "Caching Strategies",
    "CSS Transitions",
    "Debounced Search",
    "Event Hooks",
    "Fragment Navigation",
    "Granular Updates",
    "Header Inspection",
    "Hypermedia",
    "Indicators",
    "Lazy Loading",
    "Out of Band Swaps",
    "Polling",
    "Progressive Enhancement",
    "RESTful Actions",
    "Swap Strategies",
]

jinja_topics = [
    {"name": "Context variables", "detail": "Render server data into HTML."},
    {"name": "Conditionals", "detail": "Branch templates with if/else."},
    {"name": "Loops", "detail": "Repeat UI fragments for lists."},
]
jinja_alerts = [
    {"kind": "success", "message": "Macros help keep HTMX fragments consistent."},
    {"kind": "warning", "message": "Inheritance keeps your layouts DRY."},
    {"kind": "info", "message": "Macros can be shared across partials."},
]

async_runs_lock = Lock()
async_runs: dict[str, dict[str, Any]] = {}

GUIDE_DEMOS: dict[str, dict[str, Any]] = {}
_GUIDES_CACHE: dict[str, dict[str, str]] | None = None


def _server_stub(func: Any) -> str:
    source = inspect.getsource(func).strip()
    lines = [line.rstrip() for line in source.splitlines()]
    decorators = [line for line in lines if line.lstrip().startswith("@")]
    def_line = next((line for line in lines if line.lstrip().startswith("def ") or line.lstrip().startswith("async def ")), "")
    body_line = next(
        (line for line in lines if line.startswith("    ") and "return" in line),
        "    ...",
    )
    compact = decorators + [def_line, body_line]
    return "\n".join([line for line in compact if line])


def _server_full(func: Any) -> str:
    return inspect.getsource(func).strip()


def _build_guides() -> dict[str, dict[str, str]]:
    global _GUIDES_CACHE
    if _GUIDES_CACHE is not None:
        return _GUIDES_CACHE
    guides: dict[str, dict[str, str]] = {}
    for key, entry in GUIDE_DEMOS.items():
        func = entry["func"]
        guides[key] = {
            "html": entry["html"],
            "route": entry["route"],
            "server_stub": _server_stub(func),
            "server_full": _server_full(func),
        }
    _GUIDES_CACHE = guides
    return guides


def _start_async_run() -> str:
    run_id = str(uuid.uuid4())
    with async_runs_lock:
        async_runs[run_id] = {"created": datetime.now(), "results": [], "total": 5}
    for idx in range(1, 6):
        asyncio.create_task(asyncio.to_thread(_async_worker, run_id, idx))
    return run_id


def _async_worker(run_id: str, worker_id: int) -> None:
    duration = random.randint(10, 90)
    time.sleep(duration)
    payload = {
        "worker_id": worker_id,
        "duration": duration,
        "completed_at": datetime.now().strftime("%H:%M:%S"),
        "summary": f"Worker {worker_id} finished after {duration}s.",
    }
    with async_runs_lock:
        run = async_runs.get(run_id)
        if not run:
            return
        run["results"].append(payload)


@app.get("/")
def home(request: Request) -> HTMLResponse:
    now = datetime.now()
    return render(
        request,
        "index.html",
        todos=todos,
        catalog=catalog,
        q="",
        matches=catalog[:5],
        now=now,
        guides=_build_guides(),
    )


@app.get("/page/about")
def about(request: Request) -> HTMLResponse:
    return render(request, "page.html", title="About This Demo")


@app.get("/page/async-dashboard")
async def async_dashboard(request: Request) -> HTMLResponse:
    run_id = _start_async_run()
    return render(request, "async_dashboard.html", run_id=run_id)


@app.get("/hello")
def hello(request: Request, name: str = "Programmer") -> HTMLResponse:
    return render(
        request,
        "partials/hello.html",
        name=name,
        now=datetime.now(),
    )


@app.get("/jinja-demo")
def jinja_demo(request: Request) -> HTMLResponse:
    return render(
        request,
        "partials/jinja_demo.html",
        topics=jinja_topics,
        show_tip=True,
        now=datetime.now(),
    )


@app.get("/jinja-macros")
def jinja_macros(request: Request) -> HTMLResponse:
    return render(
        request,
        "partials/jinja_macros.html",
        alerts=jinja_alerts,
        now=datetime.now(),
    )


@app.get("/jinja-inheritance")
def jinja_inheritance(request: Request) -> HTMLResponse:
    return render(
        request,
        "partials/jinja_inheritance.html",
        title="Inherited Fragment",
        body="This fragment extends a base partial and overrides blocks.",
        now=datetime.now(),
    )


@app.get("/counter")
def counter(request: Request) -> HTMLResponse:
    global counter_value
    with counter_lock:
        counter_value += 1
        value = counter_value
    return render(request, "partials/counter.html", value=value)


@app.get("/search")
def search(request: Request, q: str | None = None) -> HTMLResponse:
    term = (q or "").strip().lower()
    if not term:
        matches = catalog[:5]
    else:
        matches = [item for item in catalog if term in item.lower()]
    return render(request, "partials/search_results.html", q=q or "", matches=matches)


@app.post("/form/validate")
def validate(
    request: Request,
    email: str = Form(""),
    zipcode: str = Form(""),
) -> HTMLResponse:
    email_ok = "@" in email and "." in email
    zip_ok = zipcode.isdigit() and len(zipcode) == 5
    return render(
        request,
        "partials/validation.html",
        email=email,
        zipcode=zipcode,
        email_ok=email_ok,
        zip_ok=zip_ok,
    )


@app.get("/poll")
def poll(request: Request) -> HTMLResponse:
    return render(request, "partials/poll.html", now=datetime.now())


@app.get("/lazy")
def lazy(request: Request) -> HTMLResponse:
    return render(request, "partials/lazy.html", now=datetime.now())


@app.get("/fragment")
def fragment(request: Request, tab: str = "overview") -> HTMLResponse:
    return render(request, "partials/fragment.html", tab=tab)


@app.get("/oob")
def oob(request: Request) -> HTMLResponse:
    return render(request, "partials/oob.html", now=datetime.now())


@app.get("/select-demo")
def select_demo(request: Request) -> HTMLResponse:
    return render(request, "partials/select_demo.html", now=datetime.now())


@app.get("/sync-demo")
def sync_demo(request: Request, item: str = "Alpha") -> HTMLResponse:
    sleep(1)
    return render(request, "partials/sync_demo.html", item=item, now=datetime.now())


@app.get("/params-demo")
def params_demo(request: Request, focus: str = "", debug: str = "") -> HTMLResponse:
    return render(
        request,
        "partials/params_demo.html",
        focus=focus,
        debug=debug,
        now=datetime.now(),
    )


@app.get("/preserve")
def preserve(request: Request) -> HTMLResponse:
    return render(request, "partials/preserve.html", now=datetime.now())


@app.get("/redirect-demo")
def redirect_demo() -> Response:
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = "/page/about"
    return response


@app.get("/disabled-demo")
def disabled_demo(request: Request) -> HTMLResponse:
    sleep(1)
    return render(request, "partials/disabled_demo.html", now=datetime.now())


@app.patch("/patch-demo")
def patch_demo(request: Request) -> HTMLResponse:
    return render(request, "partials/patch_demo.html", now=datetime.now())


@app.post("/validate-required")
def validate_required(request: Request, username: str = Form("")) -> HTMLResponse:
    return render(
        request,
        "partials/validate_required.html",
        username=username,
        now=datetime.now(),
    )


@app.post("/encoding-demo")
async def encoding_demo(request: Request) -> HTMLResponse:
    form = await request.form()
    return render(
        request,
        "partials/encoding_demo.html",
        content_type=request.headers.get("content-type", ""),
        fields=list(form.keys()),
        now=datetime.now(),
    )


@app.get("/select-oob")
def select_oob(request: Request) -> HTMLResponse:
    return render(request, "partials/select_oob.html", now=datetime.now())


@app.get("/request-headers")
def request_headers(request: Request) -> HTMLResponse:
    return render(
        request,
        "partials/request_headers.html",
        headers={
            "HX-Request": request.headers.get("hx-request", ""),
            "HX-Target": request.headers.get("hx-target", ""),
            "HX-Trigger": request.headers.get("hx-trigger", ""),
            "HX-Trigger-Name": request.headers.get("hx-trigger-name", ""),
            "HX-Prompt": request.headers.get("hx-prompt", ""),
            "HX-Boosted": request.headers.get("hx-boosted", ""),
            "HX-Current-URL": request.headers.get("hx-current-url", ""),
        },
        now=datetime.now(),
    )


@app.get("/response-headers/{kind}")
def response_headers(request: Request, kind: str) -> Response:
    now = datetime.now()
    response = render(request, "partials/response_headers.html", kind=kind, now=now)
    if kind == "push":
        response.headers["HX-Push-Url"] = "/?pushed=1"
    elif kind == "replace":
        response.headers["HX-Replace-Url"] = "/?replaced=1"
    elif kind == "location":
        response.headers["HX-Location"] = "/page/about?from=hx-location"
    elif kind == "refresh":
        response.headers["HX-Refresh"] = "true"
    elif kind == "reswap":
        response.headers["HX-Reswap"] = "beforeend"
    elif kind == "retarget":
        response.headers["HX-Retarget"] = "#response-retarget"
    elif kind == "reselect":
        response.headers["HX-Reselect"] = "#reselect-snippet"
    elif kind == "trigger":
        response.headers["HX-Trigger"] = json.dumps(
            {"demoEvent": {"time": now.strftime("%H:%M:%S")}}
        )
    elif kind == "trigger-after-swap":
        response.headers["HX-Trigger-After-Swap"] = json.dumps(
            {"swapEvent": {"time": now.strftime("%H:%M:%S")}}
        )
    elif kind == "trigger-after-settle":
        response.headers["HX-Trigger-After-Settle"] = json.dumps(
            {"settleEvent": {"time": now.strftime("%H:%M:%S")}}
        )
    return response


@app.get("/preload-info")
def preload_info(request: Request) -> HTMLResponse:
    return render(
        request,
        "partials/preload_info.html",
        preloaded=request.headers.get("hx-preloaded", ""),
        now=datetime.now(),
    )


@app.get("/head-support")
def head_support(request: Request) -> HTMLResponse:
    return render(request, "partials/head_support.html", now=datetime.now())


@app.get("/status-demo/{mode}")
def status_demo(request: Request, mode: str) -> HTMLResponse:
    now = datetime.now()
    if mode == "error":
        return HTMLResponse(
            templates.get_template("partials/status_demo.html").render(
                {"request": request, "status": "Error 422", "now": now}
            ),
            status_code=422,
        )
    return render(request, "partials/status_demo.html", status="OK 200", now=now)


@app.get("/morph-demo")
def morph_demo(request: Request) -> HTMLResponse:
    global morph_flip
    with morph_lock:
        morph_flip = not morph_flip
        order = ["Alpha", "Beta", "Gamma"]
        if morph_flip:
            order = list(reversed(order))
    return render(request, "partials/morph_demo.html", order=order, now=datetime.now())


@app.get("/async-dashboard/poll")
def async_dashboard_poll(request: Request, run_id: str, offset: int = 0) -> HTMLResponse:
    with async_runs_lock:
        run = async_runs.get(run_id)
        if not run:
            return render(
                request,
                "partials/async_tiles.html",
                tiles=[],
                done=True,
                next_offset=offset,
            )
        results = run["results"]
        total = run["total"]
    new_tiles = results[offset:]
    done = offset + len(new_tiles) >= total
    return render(
        request,
        "partials/async_tiles.html",
        tiles=new_tiles,
        done=done,
        next_offset=offset + len(new_tiles),
    )


@app.get("/animate")
def animate(request: Request) -> HTMLResponse:
    global animate_value
    with animate_lock:
        animate_value += 1
        value = animate_value
    return render(request, "partials/animate.html", value=value)


@app.get("/multi-swap")
def multi_swap(request: Request) -> HTMLResponse:
    return render(request, "partials/multi_swap.html", now=datetime.now())


@app.get("/items/{item_id}")
def item_detail(request: Request, item_id: str) -> HTMLResponse:
    return render(request, "partials/item_detail.html", item_id=item_id, now=datetime.now())


@app.post("/json-enc")
async def json_enc(request: Request) -> HTMLResponse:
    payload = await request.json()
    return render(request, "partials/json_enc.html", payload=payload, now=datetime.now())


@app.post("/event-header")
def event_header(request: Request) -> HTMLResponse:
    return render(
        request,
        "partials/event_header.html",
        header=request.headers.get("triggering-event", ""),
        now=datetime.now(),
    )


@app.get("/slow")
def slow(request: Request) -> HTMLResponse:
    sleep(2)
    return render(request, "partials/slow.html", now=datetime.now())


@app.get("/sse")
async def sse() -> StreamingResponse:
    async def event_stream() -> Any:
        while True:
            now = datetime.now()
            payload = (
                "event: message\n"
                f"data: <div class='result'>SSE tick {now.strftime('%H:%M:%S')}</div>\n\n"
            )
            yield payload
            await asyncio.sleep(2)

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            now = datetime.now().strftime("%H:%M:%S")
            html = (
                '<div id="ws-messages" hx-swap-oob="beforeend">'
                f'<div class="result">WS {now}: {message}</div>'
                "</div>"
            )
            await websocket.send_text(html)
    except Exception:
        await websocket.close()


@app.post("/todos")
def add_todo(request: Request, text: str = Form("")) -> HTMLResponse:
    global next_todo_id
    clean_text = text.strip()
    if not clean_text:
        return render(request, "partials/todos.html", todos=todos, error="Enter a task.")
    with todos_lock:
        todos.append({"id": next_todo_id, "text": clean_text, "done": False})
        next_todo_id += 1
    return render(request, "partials/todos.html", todos=todos, error="")


@app.put("/todos/{todo_id}")
def toggle_todo(request: Request, todo_id: int) -> HTMLResponse:
    with todos_lock:
        for todo in todos:
            if todo["id"] == todo_id:
                todo["done"] = not todo["done"]
                break
        else:
            raise HTTPException(status_code=404, detail="Todo not found")
    return render(request, "partials/todos.html", todos=todos, error="")


@app.delete("/todos/{todo_id}")
def delete_todo(request: Request, todo_id: int) -> HTMLResponse:
    with todos_lock:
        remaining = [todo for todo in todos if todo["id"] != todo_id]
        if len(remaining) == len(todos):
            raise HTTPException(status_code=404, detail="Todo not found")
        todos[:] = remaining
    return render(request, "partials/todos.html", todos=todos, error="")


@app.post("/request-info")
async def request_info(request: Request) -> HTMLResponse:
    form = await request.form()
    return render(
        request,
        "partials/request_info.html",
        headers={
            "HX-Request": request.headers.get("hx-request", ""),
            "HX-Target": request.headers.get("hx-target", ""),
            "HX-Trigger": request.headers.get("hx-trigger", ""),
            "X-Demo": request.headers.get("x-demo", ""),
        },
        params=dict(form),
    )


GUIDE_DEMOS.update(
    {
        "demo-hx-get": {
            "html": '<button hx-get="/hello" hx-target="#hello-target">Load greeting</button>',
            "route": "GET /hello",
            "func": hello,
        },
        "demo-hx-trigger": {
            "html": '<input hx-get="/search" hx-trigger="keyup changed delay:300ms" hx-target="#search-results">',
            "route": "GET /search?q=term",
            "func": search,
        },
        "demo-hx-post": {
            "html": '<form hx-post="/form/validate" hx-target="#validation">...</form>',
            "route": "POST /form/validate",
            "func": validate,
        },
        "demo-jinja": {
            "html": '{% include "partials/jinja_demo.html" %}',
            "route": "GET /jinja-demo",
            "func": jinja_demo,
        },
        "demo-jinja-macros": {
            "html": '{% import "partials/_macros.html" as ui %}',
            "route": "GET /jinja-macros",
            "func": jinja_macros,
        },
        "demo-jinja-inheritance": {
            "html": '{% extends "partials/_fragment_base.html" %}',
            "route": "GET /jinja-inheritance",
            "func": jinja_inheritance,
        },
        "demo-hx-swap": {
            "html": '<button hx-get="/counter" hx-target="#swap-demo" hx-swap="outerHTML">outerHTML</button>',
            "route": "GET /counter",
            "func": counter,
        },
        "demo-compare-swaps": {
            "html": '<button hx-get="/counter" hx-target="#compare-target-a" hx-swap="beforeend">Trigger</button>',
            "route": "GET /counter",
            "func": counter,
        },
        "demo-poll": {
            "html": '<div hx-get="/poll" hx-trigger="every 2s"></div>',
            "route": "GET /poll",
            "func": poll,
        },
        "demo-revealed": {
            "html": '<div hx-get="/lazy" hx-trigger="revealed"></div>',
            "route": "GET /lazy",
            "func": lazy,
        },
        "demo-oob": {
            "html": '<div id="badge" hx-swap-oob="true">...</div>',
            "route": "GET /oob",
            "func": oob,
        },
        "demo-push-url": {
            "html": '<button hx-get="/fragment?tab=details" hx-target="#fragment-target" hx-push-url="true">Details</button>',
            "route": "GET /fragment?tab=details",
            "func": fragment,
        },
        "demo-include": {
            "html": '<button hx-post="/request-info" hx-include="#include-note" hx-vals=\'{"source":"hx-vals"}\'></button>',
            "route": "POST /request-info",
            "func": request_info,
        },
        "demo-indicator": {
            "html": '<button hx-get="/hello" hx-indicator="#loading-indicator"></button>',
            "route": "GET /hello",
            "func": hello,
        },
        "demo-rest": {
            "html": '<button hx-delete="/todos/1" hx-confirm="Delete?"></button>',
            "route": "DELETE /todos/{id}",
            "func": delete_todo,
        },
        "demo-select": {
            "html": '<div hx-get="/select-demo" hx-select="#selected-snippet"></div>',
            "route": "GET /select-demo",
            "func": select_demo,
        },
        "demo-sync": {
            "html": '<button hx-get="/sync-demo" hx-sync="this:replace"></button>',
            "route": "GET /sync-demo",
            "func": sync_demo,
        },
        "demo-params": {
            "html": '<form hx-get="/params-demo" hx-params="not debug"></form>',
            "route": "GET /params-demo",
            "func": params_demo,
        },
        "demo-preserve": {
            "html": "<input hx-preserve=\"true\">",
            "route": "GET /preserve",
            "func": preserve,
        },
        "demo-disabled-elt": {
            "html": '<button hx-get="/disabled-demo" hx-disabled-elt="this"></button>',
            "route": "GET /disabled-demo",
            "func": disabled_demo,
        },
        "demo-redirect": {
            "html": '<button hx-get="/redirect-demo"></button>',
            "route": "GET /redirect-demo (HX-Redirect)",
            "func": redirect_demo,
        },
        "demo-patch": {
            "html": '<button hx-patch="/patch-demo" hx-target="#patch-target"></button>',
            "route": "PATCH /patch-demo",
            "func": patch_demo,
        },
        "demo-validate": {
            "html": '<form hx-post="/validate-required" hx-validate="true"></form>',
            "route": "POST /validate-required",
            "func": validate_required,
        },
        "demo-encoding": {
            "html": '<form hx-post="/encoding-demo" hx-encoding="multipart/form-data"></form>',
            "route": "POST /encoding-demo",
            "func": encoding_demo,
        },
        "demo-request": {
            "html": '<button hx-get="/slow" hx-request=\'{"timeout":1000}\'></button>',
            "route": "GET /slow",
            "func": slow,
        },
        "demo-prompt": {
            "html": '<button hx-get="/request-headers" hx-prompt="Your name?"></button>',
            "route": "GET /request-headers",
            "func": request_headers,
        },
        "demo-select-oob": {
            "html": '<div hx-get="/select-oob" hx-select-oob="#select-oob-alert"></div>',
            "route": "GET /select-oob",
            "func": select_oob,
        },
        "demo-headers": {
            "html": 'HX-Trigger: {"demoEvent":{}}',
            "route": "GET /response-headers/{kind}",
            "func": response_headers,
        },
        "demo-replace-url": {
            "html": '<button hx-get="/fragment?tab=details" hx-replace-url="true"></button>',
            "route": "GET /fragment?tab=details",
            "func": fragment,
        },
        "demo-inherit": {
            "html": '<div hx-target="#t" hx-disinherit="*"><button hx-inherit="hx-target"></button></div>',
            "route": "GET /hello",
            "func": hello,
        },
        "demo-disable": {
            "html": "<div hx-disable>...disabled HTMX subtree...</div>",
            "route": "GET /hello",
            "func": hello,
        },
        "demo-history": {
            "html": '<div hx-history-elt="#history-target"></div>',
            "route": "GET /fragment",
            "func": fragment,
        },
        "demo-history-optout": {
            "html": '<div hx-history="false"></div>',
            "route": "GET /hello",
            "func": hello,
        },
        "demo-hx-on": {
            "html": '<button hx-on::after-request="..."></button>',
            "route": "GET /hello",
            "func": hello,
        },
        "demo-jsapi": {
            "html": 'htmx.ajax("GET", "/hello", { target: "#jsapi-target" })',
            "route": "GET /hello",
            "func": hello,
        },
        "demo-classes": {
            "html": '<div class="htmx-added">New node</div>',
            "route": "GET /animate",
            "func": animate,
        },
        "demo-preload": {
            "html": '<button hx-get="/preload-info" preload="mouseover"></button>',
            "route": "GET /preload-info",
            "func": preload_info,
        },
        "demo-response-targets": {
            "html": '<button hx-get="/status-demo/error" hx-target-422="#status-error"></button>',
            "route": "GET /status-demo/{mode}",
            "func": status_demo,
        },
        "demo-head-support": {
            "html": '<div hx-get="/head-support" hx-target="#head-target"></div>',
            "route": "GET /head-support",
            "func": head_support,
        },
        "demo-sse": {
            "html": '<div hx-ext="sse" sse-connect="/sse" sse-swap="message"></div>',
            "route": "GET /sse",
            "func": sse,
        },
        "demo-ws": {
            "html": '<div hx-ext="ws" ws-connect="/ws"><form ws-send>...</form></div>',
            "route": "WS /ws",
            "func": websocket_endpoint,
        },
        "demo-morph": {
            "html": '<div hx-get="/morph-demo" hx-swap="morph"></div>',
            "route": "GET /morph-demo",
            "func": morph_demo,
        },
    }
)
