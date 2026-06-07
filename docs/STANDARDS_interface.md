# STANDARDS_interface — Interface & CLI specifications for gsheets-orm

---

## Rules

> Hard constraints for this domain. AI must follow unconditionally.

| Rule | Detail |
|------|--------|
| No magic numbers | All values must come from tokens or shared constants |
| JSON Output | All database errors must be serialized to standard error as JSON |

---

## Interface Reference

### Color System / Design Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `COLOR_ERROR` | `red` | Console error logging |
| `COLOR_SUCCESS` | `green` | Console success/info logging |

### Component Standards

| Component | Class / Pattern | Purpose |
|-----------|----------------|---------|
| `QueryResult` | Object containing rows, metadata, and status | Returned by select operations |

### Layout

| Item | Value |
|------|-------|
| `Max JSON Depth` | 4 |

---

## Edge Cases

> Only document cases that are non-obvious or have caused regressions.

- **Circular References**: `RelationshipDescriptor` does **not** detect cycles. Circular `relationship()` definitions cause infinite recursion at access time. Avoid self-referencing or mutually recursive relationships unless only one side is accessed.

---

*v0.1.8 — 2026-06-07*
