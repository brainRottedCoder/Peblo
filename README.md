# Peblo TV Mini

A small version of how **Peblo TV** actually works: a content editor uploads shows in
an internal CMS, the backend publishes a finished catalogue file, and kids browse
that file like Netflix.

```text
CMS (React)  →  API (FastAPI + Postgres)  →  catalogue.json
                                                ↓
                                         Viewer (React)
```

The kids’ app never talks to the editor database. It only reads what an admin has published.

---

## How to run

### Option A — Docker (the submission path)

```bash
cp .env.example .env
docker compose up --build
```

| Surface | URL | Who uses it |
|---|---|---|
| CMS | <http://localhost:3001> | Editors and admins |
| Viewer | <http://localhost:3002> | Kids — no login |
| API | <http://localhost:8000/health> | Health check |

First boot seeds the database and writes a **bootstrap** catalogue so the viewer is not empty. The CMS **Publish** button stays blocked until an editor fixes the seed problems listed below. That is deliberate.

### Option B — Local (faster while developing)

1. Start Postgres 16 (Docker Desktop: `docker compose up -d db`).
2. Copy `.env.example` to `.env`.
3. API:

   ```bash
   cd backend
   pip install -r requirements.txt
   alembic upgrade head
   python -m app.seed
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. CMS: `cd cms && npm install && npm run dev` → <http://localhost:5173>
5. Viewer: `cd viewer && npm install && npm run dev` → <http://localhost:5174>

The API must be on port `8000`. Both frontends call `VITE_API_URL` from `.env.example`.

---

## Accounts

| Role | Email | Password | Can publish? |
|---|---|---|---|
| Admin | `admin@peblo.local` | `admin-password` | Yes |
| Editor | `editor@peblo.local` | `editor-password` | No — CRUD only |

Change these in `.env` before any shared environment.

---

## Walk the product (five minutes)

1. Open the **CMS** and sign in as admin.
2. Open **Shows**. Search, filter, and open a title. Each show has three artwork slots
   (poster, banner, thumbnail) with live preview and editor-readable errors.
3. Open **Publish**. You will see blocking problems from the seed. The button tells you why it is disabled.
4. Open the **Viewer**. Home is a featured hero plus rows. Click a show, pick a language,
   press **Play**. Playback uses Google’s public sample MP4s — we do not ship licensed
   Peblo episodes.
5. Try **Search** on the viewer. It hits `GET /catalog/search`, not a browser-side scan of the whole file.

Sample pictures (including ones that *should* fail) live in `data/assets/`. Drop
`poster_wrong_ratio.jpg` or `banner_too_big.png` on an artwork slot to see the rejection copy.

---

## What the seed is hiding

The 95 rows across 8 shows are not clean. The validation report lists them. I did not silently “fix” the CMS copy.

1. **The Midnight Market** (`ep_0036`, Discover India with Moti) is published with **no artwork**.
2. **The Lost Kite (v2)** (`ep_9001`) is a second Hindi row for `motis-many-lives-s01e02` — same `(content_group, language)` as `ep_0004`.
3. **Season 0 trailers** (`ep_0093`, `ep_0094`) are published with only a thumbnail (warning).
4. **Rhyme Rangers** is all draft and has `section: null`.
5. **Number Nest** `ep_0078` is titled `rain on the roof` (lowercase) — warning only.

`content_group` means “these rows are language variants of one episode.” English and Hindi collapse into **one card** with language buttons. Season 0 is a trailer, not a normal season in the viewer.

---

## Decisions (short)

**Auth.** JWT, two roles, enforced on the server. Editors get CRUD. Only admins can `POST /admin/catalog/publish`. The viewer never calls `/admin/*`.

**Artwork.** Three kinds from `data/reference.json`: poster 2:3 (~600×900), banner 16:9 (~1280×720), thumbnail 16:9 (~640×360). 200 KB ceiling, aspect within 5%, at least 80% of the target pixels. Errors name the file’s actual size and tell the editor what to export. Storage is a protocol (`LocalDiskStorage` / `R2Storage`). Swap with `STORAGE_BACKEND=r2`.

**Uniqueness.** `(content_group, language)` is checked on create/update and on the validation report. Seeded rows keep a historical duplicate (`ep_9001`) so the exercise stays visible. CMS-created episodes (`external_id IS NULL`) have a partial unique index. Artwork is unique per `(show, kind)` and `(episode, kind)`.

**Indexes.** `shows(section, status, title)` plus `(status, section)` for CMS list filters. `episodes(content_group, language)`, `(status, show_id)`, `title`. `publish_runs(started_at)`. Viewer search does **not** hit these tables — it reads the published file.

**CMS.** TanStack Query, because the desk is a cache-invalidation problem (list → edit → publish). Loading, empty, error, and 403 states are all handled. The login screen has a decorative 3D orbit; all labels and controls stay in HTML.

**Viewer.** Netflix-style home: banner on the hero, posters on rows, thumbnails on episode lists. Images show a skeleton while they load. Trailers stay out of Season 1.

---

## Part E — written reasoning

### How publish is atomic (and what happens if the process dies)

Concurrent publishes take a Postgres session advisory lock, so two admin clicks serialize. A `publish_runs` row starts as `started`.

1. Write a **versioned** file first: `catalogues/{run_id}.json`.
2. Replace the **live** object with `put_atomic`: sibling `.tmp` + `fsync` + `os.replace` (POSIX and Windows).
3. Flip a one-line pointer (`catalogues/current.json`) last.

If the process dies during the versioned write or the temp write, readers still see the previous full file. If it dies after `os.replace`, the new catalogue is already complete — we mark that run `success` even if the pointer write fails, so history matches what kids see. We never truncate-and-overwrite the live path. A blocked run is recorded; the live file is unchanged. A second publish of the same catalogue (hash ignoring `run_id` / `published_at`) reuses the previous object and records an idempotent success.

### Storage: local disk → Cloudflare R2

Set `STORAGE_BACKEND=r2` and the `R2_*` keys in `.env`. Call sites do not change. `R2Storage.put_atomic` uploads a staging key, then `CopyObject` onto the live key so a crash mid-upload cannot replace `catalogue.json` with a partial body. Artwork URLs come from `R2_PUBLIC_BASE_URL` (or fall back through `/media`).

### Search

`GET /catalog/search` filters the **published file** in process: substring on show title, episode title, and category; `category` / `language` / `section` AND together. Fine for this catalogue (~8 shows). It will feel slow and memory-heavy around **50–100k grouped episodes** on a single API box.

Next step: Postgres `tsvector` or Typesense/Meilisearch fed by the same publish job — not a live query of draft rows, and not a browser-side scan of the whole file.

### Why a pre-published file at all?

The kids’ UI is read-heavy. It should not depend on CMS draft state, a Postgres join shape, or a content editor mid-save. Publish is the contract: what you reviewed is what ships.

Where it bites: a published show that an editor just unpublished stays live until the next successful publish; search cannot see drafts; and a bad publish (if we allowed one) would be global. Versioned files make that last case recoverable.

### What I left out, and AI

**Skipped (on purpose).** No audit log or dry-run diff (stretch). Rollback is almost free — versioned objects already exist — but I did not ship a CMS button for it. A table-wide unique on `(content_group, language)` would reject the seeded duplicate and hide the exercise; the partial CMS index + API check is the compromise.

**AI.** Built in Cursor with Grok. I accepted the scaffold (FastAPI layout, compose shape, Vite apps). I rejected generic “Netflix black + red + Inter” as the only viewer look, auto-dropping the seed duplicate, and client-side-only artwork checks. Validation copy and the atomic write sequence are mine.

---

## Operability (Part D)

**Health.** `GET /health` is liveness. `GET /health/ready` checks the database and storage.

**Alert.** I would page on `publish_runs.outcome = failed` (and a stuck `started` older than a few minutes). `/health` staying green is not enough: the kids’ app would keep serving yesterday’s file while an editor believes they published. Secondary: `/health/ready` failing.

**Secrets.** `.env` is local only. In production: `SECRET_KEY`, `DATABASE_URL`, seed passwords, and R2 keys live in GitHub Environments / GCP Secret Manager / AWS SSM and are injected at task start. Rotate the JWT secret and the two CMS passwords independently. Never bake them into images. Every variable is listed in `.env.example`.

**CI.** GitHub Actions lints, tests, and builds the three images. The `deploy` job is a documented no-op — there is no cloud account. A real ship would push images, run `alembic upgrade`, roll the API, wait for `/health/ready`, then shift traffic.

**Viewer media.** Show posters and banners are packed stills in `data/show-art/` (photographs prepared for this take-home). Playback uses Google’s public sample MP4s (`Big Buck Bunny`, `Sintel`, and similar) from `app/playback.py`. Swap that module for real files in R2 when you have them.

---

## Time (rough)

| Part | Hours |
|---|---|
| A Backend + tests | 3 |
| B CMS | 1.5 |
| C Viewer | 1.5 |
| D Compose / CI / seed forensics | 1.5 |
| E README | 0.5 |

CMS polish (login orbit, poster grid) and viewer Play happened after the core path worked.

---

## Tests

```bash
cd backend && pytest -q
```

Risky bits covered: artwork reject/accept over HTTP, search filter composition, atomic + idempotent publish, JWT role guards, content-group collapse, and season 0.

---

## Repo map

| Path | What it is |
|---|---|
| `backend/` | FastAPI, Alembic, validation, publish, tests |
| `cms/` | Internal editor (Vite + React + TanStack Query) |
| `viewer/` | Kids browse + Play (reads `/catalog` only) |
| `data/seed_shows.json` | 95 episode rows |
| `data/reference.json` | Sections, languages, artwork specs |
| `data/assets/` | Good and bad sample images |
| `docker-compose.yml` | db, api, cms `:3001`, viewer `:3002` |
