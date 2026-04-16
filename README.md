# jex

An interactive JSON explorer that runs in your terminal.

Load any JSON file (or pipe it from stdin), and browse it as a collapsible tree with live search, keyboard navigation, and a side panel that shows the value under your cursor. Think `less`, but built for JSON.

```
┌─ sample.json ─────────────────┐ ┌──────────────────────┐
│ ▼ sample.json                 │ │ {                    │
│   app: "jex"                  │ │   "name": "Ada ...", │
│   version: "0.1.0"            │ │   "role": "lead",    │
│   active: true                │ │   "commits": 142     │
│   ▼ maintainers [2]           │ │ }                    │
│     ▶ 0 {3}   ← cursor here   │ │                      │
│     ▶ 1 {3}                   │ │                      │
│   ▼ config {3}                │ │                      │
│     theme: "dark"             │ │                      │
└───────────────────────────────┘ └──────────────────────┘
 path: $.maintainers[0]   / search · e expand · c collapse · y copy · q quit
```

## Why

If you've ever piped an API response into `jq` and then scrolled through 2000 lines of JSON trying to find one key, this is for you. `jex` gives you:

- A collapsible tree view of any JSON structure
- Live search as you type
- The current dot-path of your cursor (`$.users[0].profile.email`)
- A side panel with the full value under the cursor
- Clipboard copy (`y`) for any value or subtree
- Stdin support so you can pipe curl/jq output straight into it

## Install

```bash
git clone https://github.com/yourusername/jex.git
cd jex

python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -e ".[clipboard]"     # the [clipboard] extra enables 'y' to copy
```

**Requires Python 3.10+.**

## Usage

```bash
# open a file
jex sample.json

# pipe from stdin
curl -s https://api.github.com/repos/textualize/textual | jex

# explicit stdin
cat data.json | jex -
```

### Keybindings

| Key | Action |
|---|---|
| `↑` / `↓` | Navigate nodes |
| `→` / `←` | Expand / collapse node |
| `/` | Focus search input |
| `esc` | Clear search, return to tree |
| `e` | Expand the entire tree |
| `c` | Collapse everything to the top level |
| `y` | Copy the selected value to clipboard |
| `q` | Quit |

## Project Structure

```
jex/
├── jex/
│   ├── __init__.py     # version
│   ├── app.py          # the Textual app (tree, detail panel, search)
│   └── cli.py          # Click entry point, stdin/file loading
├── sample.json         # try it out: jex sample.json
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

## How it works

The core is a single Textual `App` subclass. When you open a file, `jex` recursively walks the JSON structure and builds a `Tree` widget — each node carries its original key and value in its `data` attribute. The right-hand panel is a `Static` widget that re-renders whenever the cursor moves, pulling the value straight from the selected node. Search is a plain DFS over the tree that expands every ancestor of the first match so the hit is visible.

Textual handles all the async event loop and reactive rendering, which is why the whole app fits in ~200 lines without feeling cramped.

## Roadmap

- [ ] JSONPath / jq-style filter expressions
- [ ] YAML and TOML support
- [ ] Theme switcher (dark / light / solarized)
- [ ] Open URLs directly (`jex https://api.example.com/data`)
- [ ] Tests with `textual.pilot`
- [ ] Schema inference panel

## License

MIT
# Jex
