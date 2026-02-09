# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI + HTMX teaching application. Each card on the home page demonstrates a specific HTMX feature with a server-rendered fragment, allowing users to inspect the request/response cycle in browser devtools.

## Commands

### Run the development server
```bash
uvicorn main:app --reload
```

### Install dependencies
```bash
# Using pip
pip install -r requirements.txt

# Using uv
uv pip install -r requirements.txt
```

### Run tests
```bash
pytest test_main.py -v
```

## Architecture

### Core Pattern
All HTML is server-rendered using Jinja2 templates. HTMX handles client-side partial updates by swapping HTML fragments returned from FastAPI endpoints.

### File Structure
- `main.py` - Single-file FastAPI application containing all route handlers and in-memory state
- `templates/layout.html` - Base template with HTMX libraries and shared JavaScript
- `templates/index.html` - Home page with all demo cards (extends layout.html)
- `templates/partials/` - Fragment templates returned by HTMX requests
- `templates/partials/_macros.html` - Shared Jinja macros
- `templates/partials/_fragment_base.html` - Base template for inherited fragments
- `static/style.css` - Application styles

### Route Pattern
Each HTMX demo follows this pattern:
1. Route handler in `main.py` receives the request
2. Handler calls `render()` with a partial template from `templates/partials/`
3. HTMX swaps the returned HTML fragment into the target element

### GUIDE_DEMOS Dictionary
The `GUIDE_DEMOS` dict in `main.py` maps demo card IDs to their HTML snippets, routes, and handler functions. This data is exposed to the frontend as `window.HTMX_GUIDES` for the "How to implement" panels.

### State
In-memory state uses thread locks for concurrent access:
- `counter_value` - Simple counter demo
- `todos` - Todo list for CRUD demos
- `morph_flip` - Toggle for morph demo ordering
