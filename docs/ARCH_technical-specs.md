# ARCH_technical-specs — Core architecture and data models for gsheets-orm

---

## Rules
> Hard constraints. AI must follow these unconditionally.

| Rule | Detail |
|------|--------|
| Schema Definition | Every table schema must define primary keys and field data types |
| Safe Updates | Update operations must acquire read-before-write or check version tags to prevent concurrent overwrite |

---

## Reference

### Architecture Layers

| Layer | Module | Responsibility | Input | Output |
|-------|--------|----------------|-------|--------|
| Declarative Base | `schema/declarative.py` | Model registration, schema introspection | Class definition | `_columns`, `_primary_keys` registry |
| Types | `types/core_types.py` | Bidirectional type casting | Raw cell string / Python value | Python value / sheet string |
| ORM Core | `orm/session.py`, `orm/query.py`, `orm/joinedload.py` | Query parsing, transaction state, identity map, eager loading | Query DSL / Options | Batched cell payloads / pre-populated models |
| Data Mapper | `orm/mapper.py` | Row ↔ model translation | Sheet row list / model instance | Model `attrs` dict / row list |
| Dialect | `engine/dialect.py` | gspread API calls, rate limit retry | Batched cell payloads | Google API response |
| Engine | `engine/base.py` | Auth + connection management | URI string | Authenticated `gspread.Client` |

### Data Models

| Model Concept | Implementation | Notes |
|---------------|---------------|-------|
| `Column` | Descriptor (`__get__`, `__set__`, `__set_name__`) | Tracks per-instance values in `_values` dict. Supports min_length, max_length, and regex validation on assignment. |
| `ForeignKey` | Metadata marker on `Column` | Resolved by `RelationshipDescriptor` at access time |
| `Base` | `__init_subclass__` hook | Registers `__tablename__` → class in global `_registry` |
| `BinaryExpression` | Operator overload return type | Used by `Query.filter()` for lazy evaluation. Supported operators: `==`, `!=`, `<`, `<=`, `>`, `>=`, `contains`, `startswith`, `endswith`, `like` (case-insensitive substring). String operators are None-safe — a `None` column value is treated as `""`. |
| `RelationshipDescriptor` | Descriptor, lazy-loads via `Session.query()` | Detects M:1 vs 1:M by inspecting FK direction. Cannot be passed as a kwarg to `__init__` — must be assigned post-construction (`instance.rel = value`) |
| `JoinedLoad` | Query option, resolved in `Query.all()` | Eagerly loads relationships to avoid N+1 query problem. Pre-populates related instances directly into the `_values` dictionary of target models using one extra query. |

### State Registry

| State | Owner | Cleared on |
|-------|-------|-----------|
| `_new` | `Session` | `commit()` |
| `_dirty` | `Session` | `commit()` |
| `_deleted` | `Session` | `commit()` |
| `_identity_map` | `Session` | Never (lives for session lifetime) |
| `_snapshots` | `Session` | Cleared on `commit()` / Restored to `_values` on `rollback()` |
| `_registry` | `schema/declarative.py` module | `clear_registry()` — test use only |
| `_values` | Model instance | Per-instance, mutated by descriptors |

---

## Edge Cases

- **Rate Limit Exhaustion**: `dialect.py` retries with exponential backoff (max 8 attempts) on HTTP 429. **Invariant**: any method decorated with `@retry_on_rate_limit` must `raise` `APIError` directly — never catch and re-wrap it as `DialectError`. Wrapping defeats the decorator's `except APIError` branch and silently disables retry.
- **Missing Worksheet**: `commit()` writes headers first if `fetch_worksheet_data` returns empty.
- **Concurrent Overwrites**: `Session` performs read-before-write to resolve row numbers. No lock is held — last writer wins.
- **Circular Relations**: `RelationshipDescriptor` does not detect cycles. Circular `relationship()` definitions will cause infinite recursion. See `STANDARDS_interface.md`.
- **Identity Map Manual Clear**: `session._identity_map.clear()` is a valid pattern to force a live re-query (e.g., in tests). It does not reset `_new`, `_dirty`, or `_deleted` — only the cache of already-committed objects.
- **Composite Primary Keys Auto-Generation**: Automatic primary key generation during `commit()` supports composite keys. However, each column in a composite primary key must define a `prefix` (e.g. `Column(Integer, primary_key=True, prefix="EMP")`) so that the next key can be generated independently. If a column in a composite primary key is missing its value and has no `prefix`, a `ValueError` is raised.
- **Joinedload Eager Loading**: Using `.options(joinedload(Model.relation))` forces eager loading. It bypasses `RelationshipDescriptor`'s default lazy load by running exactly one query for the related table and grouping/mapping the instances in memory before returning results.

---

*v0.1.7 — 2026-06-07*
