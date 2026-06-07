# REF_developer-reference — Developer reference tables

> Reference only. Rules live in `GUIDE_developer.md`.

---

## Reference

### Naming Conventions

| Type | Rule | Do | Don't |
|------|------|----|-------|
| Functions | `snake_case`, verb + noun | `get_item_by_id`, `fetch_schema` | `do_stuff`, `thing` |
| Variables | `snake_case`, intent first, avoid generic names | `item_list`, `config_data` | `data`, `tmp` |
| Booleans | prefix `is_` / `has_` / `can_` / `should_` | `is_valid`, `has_items` | `flag`, `state` |
| Event handlers | prefix `handle_` + target + event | `handle_submit_click`, `handle_filter_change` | `on_click`, `click_handler` |
| Async functions | `snake_case`, action-oriented, name what is fetched or saved | `fetch_item_list`, `save_user_settings` | `get_data`, `load_stuff` |
| Data objects (Classes) | `PascalCase`, context + subject + type | `UserAuthInfo`, `SystemStateMap` | `Payload`, `ThingObject` |
| Files (Modules) | short, all-lowercase, use underscores for readability | `storage_manager.py`, `board_renderer.py` | `utils.py`, `misc.py` |

### Commands

| Command | Purpose |
|---------|---------|
| `pip install -e .` | Install package in editable development mode |
| `pytest tests/unit/` | Run unit tests only |
| `pytest tests/integration/ -v` | Run integration tests (requires `GSHEETS_CREDENTIALS_PATH` + `GSHEETS_SPREADSHEET_ID`) |
| `pytest` | Run all tests; integration tests self-skip if env vars absent |
| `python -m build` | Build distributions |
| `python bump_version.py` | Sync version across all files |

### Version

| Item | Detail |
|------|--------|
| Source of truth | `setup.py` |
| Bump command | `python bump_version.py` |
| Files auto-updated | `setup.py`, `AGENTS.md`, `docs/*.md` |

### Google Sheets API Reference

| Item | Value | Notes |
|------|-------|-------|
| Read request limit | 60 per minute per user | Standard Google API quota limit |
| Write request limit | 60 per minute per user | Standard Google API quota limit |
| Max cells per sheet | 10,000,000 | Google Sheets limit |

---

*v0.1.2 — 2026-06-07*
