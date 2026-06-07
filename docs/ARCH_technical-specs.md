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
| ORM Core | `orm/session.py`, `orm/query.py` | Query parsing, transaction state, identity map | Query DSL | Batched cell payloads |
| Data Mapper | `orm/mapper.py` | Row ↔ model translation | Sheet row list / model instance | Model `attrs` dict / row list |
| Dialect | `engine/dialect.py` | gspread API calls, rate limit retry | Batched cell payloads | Google API response |
| Engine | `engine/base.py` | Auth + connection management | URI string | Authenticated `gspread.Client` |

### Data Models

| Model Concept | Implementation | Notes |
|---------------|---------------|-------|
| `Column` | Descriptor (`__get__`, `__set__`, `__set_name__`) | Tracks per-instance values in `_values` dict |
| `ForeignKey` | Metadata marker on `Column` | Resolved by `RelationshipDescriptor` at access time |
| `Base` | `__init_subclass__` hook | Registers `__tablename__` → class in global `_registry` |
| `BinaryExpression` | Operator overload return type | Used by `Query.filter()` for lazy evaluation |
| `RelationshipDescriptor` | Descriptor, lazy-loads via `Session.query()` | Detects M:1 vs 1:M by inspecting FK direction |

### State Registry

| State | Owner | Cleared on |
|-------|-------|-----------|
| `_new` | `Session` | `commit()` |
| `_dirty` | `Session` | `commit()` |
| `_deleted` | `Session` | `commit()` |
| `_identity_map` | `Session` | Never (lives for session lifetime) |
| `_registry` | `schema/declarative.py` module | `clear_registry()` — test use only |
| `_values` | Model instance | Per-instance, mutated by descriptors |

---

## Edge Cases

- **Rate Limit Exhaustion**: `dialect.py` retries with exponential backoff (max 5 attempts) on HTTP 429.
- **Missing Worksheet**: `commit()` writes headers first if `fetch_worksheet_data` returns empty.
- **Concurrent Overwrites**: `Session` performs read-before-write to resolve row numbers. No lock is held — last writer wins.
- **Circular Relations**: `RelationshipDescriptor` does not detect cycles. Circular `relationship()` definitions will cause infinite recursion. See `STANDARDS_interface.md`.

---

*v0.1.2 — 2026-06-07*
