# Public JAS map schema

| Field | Allowed values | Meaning |
| --- | --- | --- |
| `type` | `cluster`, `object`, `source-layer`, `support-layer`, `unknown` | Catalog noun kind |
| `universe` | `live`, `leftover`, `ghost`, `unknown` | Whether the source is in force |
| `status` | `stub`, `verified`, `stale` | Citation/freshness state |
| `access_tier` | `public`, `private`, `owner-only`, `unknown` | Distribution boundary |

Public cards must cite public repository sources. Private source bytes and
installed state are never copied into this map.

