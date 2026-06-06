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

### Data Flow layers

| Layer | Responsibility | Input | Output |
|-------|----------------|-------|--------|
| ORM Core | Query parsing, transaction state | Query DSL | Raw Cell Payload |
| Sheets Client | Batch API requests, rate limit backoff | Raw Cell Payload | Google API Response |

---

## Edge Cases

- **Rate Limit Exhaustion**: Queue updates and write in chunks.

---

*v0.1.0 — 2026-06-06*
