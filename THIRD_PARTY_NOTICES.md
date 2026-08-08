# Third-party notices

This repository vendors snapshots of third-party Codex plugins so that the same reviewed files can be installed on multiple computers. The Git commit pins the exact snapshot stored here.

| Plugin | Snapshot | Upstream | Declared license | Notes |
| --- | --- | --- | --- | --- |
| Build Web Apps | 0.2.0 | [openai/plugins](https://github.com/openai/plugins) | MIT | Locally curated subset focused on frontend, Stripe and Supabase/Postgres workflows. |
| Test Android Apps | 0.1.2 | [openai/plugins](https://github.com/openai/plugins) | MIT | Includes upstream source pins in `plugin.lock.json`; the Android emulator QA skill also carries an Apache-2.0 license file. |
| Zotero | 0.1.3 | [openai/plugins](https://github.com/openai/plugins) | MIT | Vendored plugin snapshot. |
| HyperFrames | 0.2.0 | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | Vendored plugin snapshot. |
| Superpowers (archive only) | 5.1.3 | [obra/superpowers](https://github.com/obra/superpowers) | MIT | Preserved under `archive/`; never installed automatically. |

The plugin metadata and any license files included inside the vendored directories remain authoritative for those files. Before making this repository public or redistributing a modified snapshot, re-check the current upstream license and attribution requirements.
