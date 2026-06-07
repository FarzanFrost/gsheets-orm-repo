# Refactor TODO — gsheets-orm

> Working note for current refactoring tasks. Canonical rules: `GUIDE_developer.md`.

---

## ✅ Phase 1: Initial Repository Setup (Done)
- [x] Initialize documentation structure

---

## ✅ Phase 2: Core Architecture (Done)
- [x] Define core types with bidirectional casting (`types/core_types.py`)
- [x] Build `Column` descriptor + `ForeignKey` + `BinaryExpression` (`schema/columns.py`)
- [x] Build declarative `Base` with subclass registry (`schema/declarative.py`)
- [x] Implement `Engine` + URI parsing + dual-auth (`engine/base.py`)
- [x] Implement `Dialect` with gspread wrapper + retry decorator (`engine/dialect.py`)
- [x] Implement `Query` builder with soft-delete auto-filter (`orm/query.py`)
- [x] Implement `Session` Unit of Work + Identity Map + batch commit (`orm/session.py`)
- [x] Implement `RelationshipDescriptor` lazy-loading (`orm/relationships.py`)
- [x] Implement `DataMapper` row ↔ model translation (`orm/mapper.py`)
- [x] Unit tests for all modules (23 tests passing)
- [x] Integration test scaffold with env-var skip guard
- [x] CI pipeline wired: `unit-tests` (3.8–3.12) + `integration-tests` (3.11) jobs; secrets `GOOGLE_CREDENTIALS_JSON` / `TEST_SPREADSHEET_ID` mapped to env vars
- [x] Integration test scenarios expanded: 1:M (lazy loading), M:N (mapping table), self-referencing FK, batch commit across 3 sheets (`test_integration.py`)
- [x] Fixed `@retry_on_rate_limit` decorator bypass — dialect methods now re-raise `APIError` directly instead of wrapping it as `DialectError` (`engine/dialect.py`)

---

## 🧊 Phase 3: Backlog

- [x] **Composite primary keys**: `get_pk_value` returns a tuple but `generate_next_key` only handles single columns.
- [x] **Eager loading**: Add `joinedload()` / `contains_eager()` option to `Query` to batch-fetch relations in one round trip.
- [x] **Pagination**: Add `.offset(n)` to `Query` for cursor-based paging over large sheets.
- [x] **Column-level validation**: `nullable=False` is enforced on set, but no `min_length`, `max_length`, or regex validators exist yet.
- [x] **Session rollback**: `Session.rollback()` not implemented — currently the only recovery path is re-instantiating the session.
- [x] **Deprecate `setup.py`**: Migrate from `setup.py` to `pyproject.toml`-only build when Python 3.8 support is dropped.

---

## Safety & Verification
1. Zero-Loss Refactor Protocol: No behavioral changes allowed.
2. Test before and after every major edit.
3. Build must pass before commit.

---

*v0.1.7 — 2026-06-07*
