# Peblo TV Mini

Internal CMS → FastAPI + Postgres → atomic `catalogue.json` → kids’ browse UI.

```
CMS :3001 / :5173  →  API :8000  →  catalogue.json
                                      ↓
                              Viewer :3002 / :5174
```

## How to run

```bash
cp .env.example .env
docker compose up --build
```

Then:

| Surface | URL | Sign in |
|---|---|---|
| CMS | http://localhost:3001 | `admin@peblo.local` / `admin-password` |
| Viewer | http://localhost:3002 | none — public catalogue only |
| API | http://localhost:8000/health | — |
| Editor (no publish) | same CMS | `editor@peblo.local` / `editor-password` |

Sample pictures (including ones that *should* fail) live in `data/assets/`. Use them on a show’s artwork slots.

Without Docker: start Postgres 16, `cd backend && pip install -r requirements.txt && alembic upgrade head && python -m app.seed && uvicorn app.main:app --reload`, then `npm install && npm run dev` in `cms/` (5173) and `viewer/` (5174).

## What the seed is hiding

The 95 rows are not clean. The validation report lists them; I did not silently “fix” the CMS copy.

1. **`ep_0036` The Midnight Market** (Discover India with Moti) is *published* with no artwork.
2. **`ep_9001` The Lost Kite (v2)** is a second Hindi row for `motis-many-lives-s01e02` — same `(content_group, language)` as `ep_0004`.
3. **Season 0 trailers** (`ep_0093`, `ep_0094`) are published with only a thumbnail.
4. **Rhyme Rangers** is all draft and has `section: null`.
5. **Number Nest** `ep_0078` is titled `rain on the roof` (lowercase) — warning only.

`docker compose up` still gives a working viewer: seed writes a **bootstrap** catalogue from *valid* published rows so kids aren’t staring at an empty home. The CMS **Publish** button stays disabled until an editor resolves the blocking items. That is deliberate — first-run operability without lying about data quality.

## Decisions

**Auth.** JWT, two roles, enforced on the server. Editors get CRUD. Only admins can `POST /admin/catalog/publish`. The viewer never calls `/admin/*`.

**Artwork.** Three kinds, 200 KB ceiling, aspect within 5%, minimum 80% of the target pixel size. Errors name the file’s actual pixels and tell the editor what to export. Storage is a protocol (`LocalDiskStorage` / `R2Storage`); swap with `STORAGE_BACKEND=r2`.

**Uniqueness.** `(content_group, language)` is enforced on create/update and on the validation report. Seeded rows keep a historical duplicate (`ep_9001`) so the exercise stays visible. CMS-created episodes (`external_id IS NULL`) have a partial unique index. Artwork is unique per `(show, kind)` and `(episode, kind)`.

**Indexes.** `shows(section, status, title)` plus `(status, section)` for the list filters. `episodes(content_group, language)`, `(status, show_id)`, `title`. `publish_runs(started_at)`. Search does not hit these tables — it reads the published file.

---

## Part E — written reasoning

**Atomic publish.** Concurrent publishes take a Postgres session advisory lock, so two admin clicks serialize. A run row is inserted as `started`. The JSON is written to `catalogues/{run_id}.json` first. The live object is then replaced with `put_atomic`: sibling `.tmp` + `fsync` + `os.replace` on disk (POSIX and Windows). A one-line pointer (`catalogues/current.json`) flips last. If the process dies during the versioned write or the temp write, readers still see the previous full file. If it dies after `os.replace`, the new catalogue is already complete — we mark that run `success` even if the pointer write fails, so history matches what kids see. We never truncate-and-overwrite the live path. A blocked run is recorded; the live file is unchanged. A second publish of the same catalogue (hash ignoring `run_id` / `published_at`) reuses the previous object and records an idempotent success.

**Local disk → R2.** Set `STORAGE_BACKEND=r2` and the `R2_*` keys. Call sites stay the same. `R2Storage.put_atomic` uploads a staging key, then `CopyObject` onto the live key so a crash mid-upload cannot replace `catalogue.json` with a partial body. Artwork URLs come from `R2_PUBLIC_BASE_URL` (or fall back through `/media`).

**Search.** `GET /catalog/search` filters the **published file** in process (substring on show title, episode title, category; `category` / `language` / `section` AND together). Fine for this catalogue (~8 shows). It will feel slow and memory-heavy around **50–100k grouped episodes** on a single API box. Next step: Postgres `tsvector` or Typesense/Meilisearch fed by the same publish job — not a live query of draft rows, and not a browser-side scan of the whole file.

**Why a pre-published file?** The kids’ UI is read-heavy and should not depend on CMS draft state, Postgres join shape, or a content editor mid-save. Publish is the contract: what you reviewed is what ships. The bite: a published show that an editor just unpublished is still live until the next successful publish; search cannot see drafts; and a bad publish (if we allowed one) would be global. Versioned files make that last case recoverable.

**Left out, on purpose.** No audit log / dry-run diff (stretch). Rollback API is almost free — versioned objects already exist — but I did not ship a CMS button for it. A table-wide unique on `(content_group, language)` would reject the seeded duplicate and hide the exercise; the partial CMS index + API check is the compromise. I used TanStack Query because the CMS is a cache-invalidation problem (list → edit → publish) and it handles loading/error without extra ceremony.

**AI.** Built in Cursor with Grok. I accepted the scaffold (FastAPI layout, compose shape, Vite apps). I rejected generic “Netflix black + red + Inter” viewer styling, auto-dropping the seed duplicate, and client-side-only artwork checks. Validation copy and the atomic write sequence are mine.

**Alert.** I would page on **`publish_runs.outcome = failed`** (and a stuck `started` older than a few minutes). `/health` staying green is not enough: the kids’ app would keep serving yesterday’s file while an editor believes they published. Secondary: `/health/ready` failing (DB or storage).

**Viewer media.** Show posters/banners are packed stills in `data/show-art/` (cinematic photographs generated for this take-home, plus Unsplash extras for episode thumbs). Playback uses Google’s public sample MP4s (`Big Buck Bunny`, `Sintel`, etc.) so Play actually works — we do not ship licensed Peblo episodes. Swap `app/playback.py` for real files in R2 when you have them.

**Secrets in production.** `.env` is local only. In prod: `SECRET_KEY`, `DATABASE_URL`, seed passwords, and R2 keys in GitHub Environments / GCP Secret Manager / AWS SSM, injected at task start. Rotate the JWT secret and the two CMS passwords independently. Never bake them into images.

**Deploy (CI).** The workflow lints, tests, and builds the three images. The `deploy` job is a documented no-op — there is no cloud account. A real ship would push images, run `alembic upgrade`, roll the API, wait for `/health/ready`, then shift traffic.

## Time (rough)

| Part | Hours |
|---|---|
| A Backend + tests | 3 |
| B CMS | 1.5 |
| C Viewer | 1.5 |
| D Compose / CI / seed forensics | 1.5 |
| E README | 0.5 |

## Tests

```bash
cd backend && pytest -q
```

Risky bits covered: artwork reject/accept over HTTP, search filter composition, atomic + idempotent publish, JWT role guards, content-group collapse + season 0.
