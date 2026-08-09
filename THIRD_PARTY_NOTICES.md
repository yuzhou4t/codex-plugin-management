# Third-party notices

This repository vendors snapshots of third-party Codex Skills and plugins so that the same reviewed files can be installed on multiple computers. The Git commit pins the exact snapshot stored here.

## Standalone Skills

| Skill | Reviewed upstream revision | Upstream | Declared license | Notes |
| --- | --- | --- | --- | --- |
| `gsap-*` (8 Skills) | `aed9cfd3277740755f6bfc1155c7aa645403b760` | [greensock/gsap-skills](https://github.com/greensock/gsap-skills) | MIT | Local files were byte-for-byte equivalent to this revision when imported. |
| `storage-analyzer` | `651a45affc65919c0e3facc6124f1656d43c4ad2` | [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) | MIT | Local files were byte-for-byte equivalent to this revision when imported. |
| `aihot` | compared with `651a45affc65919c0e3facc6124f1656d43c4ad2` | [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) | MIT upstream | Locally adapted version; it intentionally differs from the reviewed upstream revision. |
| `hv-analysis` | compared with `651a45affc65919c0e3facc6124f1656d43c4ad2` | [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) | MIT upstream | Locally adapted version; it intentionally differs from the reviewed upstream revision. |
| `ima-skill` | local package metadata `1.1.8` | [IMA](https://ima.qq.com) | No license file included in the installed package | Kept in this private synchronization repository; re-check redistribution terms before making it public. |

Copies of the MIT license texts reviewed for GSAP Skills and Khazix Skills are stored under `third_party/licenses/`.

## Plugins

| Plugin | Snapshot | Upstream | Declared license | Notes |
| --- | --- | --- | --- | --- |
| Build Web Apps | 0.2.0 | [openai/plugins](https://github.com/openai/plugins) | MIT | Locally curated subset focused on frontend, Stripe and Supabase/Postgres workflows. |
| Test Android Apps | 0.1.2 | [openai/plugins](https://github.com/openai/plugins) | MIT | Includes upstream source pins in `plugin.lock.json`; the Android emulator QA skill also carries an Apache-2.0 license file. |
| Zotero | 0.1.3 | [openai/plugins](https://github.com/openai/plugins) | MIT | Vendored plugin snapshot. |
| HyperFrames | 0.2.0 | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | Vendored plugin snapshot. |
| Superpowers (archive only) | 5.1.3 | [obra/superpowers](https://github.com/obra/superpowers) | MIT | Preserved under `archive/`; never installed automatically. |

The plugin metadata and any license files included inside the vendored directories remain authoritative for those files. Before making this repository public or redistributing a modified snapshot, re-check the current upstream license and attribution requirements.
