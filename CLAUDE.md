# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Kodi subtitle addon (`service.subtitles.a4ksubtitles`) written in Python, aggregating results from
multiple subtitle providers (Addic7ed, BSPlayer, OpenSubtitles, Podnadpisi.NET, SubDL, SubSource).

This is a personal fork of `a4k-openproject/a4kSubtitles`. See the **"This fork"** section in
`README.md` for the full rationale and known limitations — in short: upstream's manual search was
a disabled stub and aborted the entire search whenever automatic IMDB matching failed, which broke
badly for anime. This fork wires manual search into the real flow and relaxes those hard-abort
conditions so providers that don't need an IMDB id still work.

## Commands

```sh
pip install -r requirements.txt      # requests, pytest, flake8, coverage

flake8                                 # lint (config in .flake8; max-complexity=10, line length 200)

pytest -v -s --log-level=DEBUG         # run the full suite
pytest tests/test_suite.py::test_opensubtitles -v -s   # run a single test
coverage run -m pytest -v -s --log-level=DEBUG && coverage report   # with coverage (.coveragerc)

git config core.hooksPath .githooks    # one-time: enables addons.xml/changelog auto-gen on commit
```

**Tests hit real provider APIs over the network — there is no HTTP mocking.** Expect failures
offline or without credentials. Some tests need API keys as env vars (`A4KSUBTITLES_SUBSOURCE_APIKEY`,
referenced but currently commented out for `A4KSUBTITLES_SUBDL_APIKEY`); OpenSubtitles tests run
search anonymously and skip the download step entirely when `A4KSUBTITLES_TESTRUN=true` (the default,
set in `tests/test_suite.py`). A local `.env` (gitignored) can hold real credentials for manual/local
runs; the addon itself never reads `.env` — Kodi settings are the only source of credentials at runtime.

### Commit convention (enforced by `scripts/validate_commit.py` in CI)

Only three commit message shapes are allowed on `master`: `chore: ...`, `test: ...`, or
`release: vMAJOR.MINOR.PATCH`. A `release:` commit's version must match `addon.xml`'s `version`
attribute exactly, and `addon.xml`'s `<news>` block must start with a matching `[vX.Y.Z]:` entry.
PRs must be a single commit (CI rejects more than one). `chore:`-prefixed commits skip lint/tests in CI.

### Local install-to-Kodi workflow (this fork, not upstream)

This fork is developed by editing the repo directly and copying changed files into Kodi's live addon
folder — there is no zip/repo-based install/reload cycle:
- Bump `version` in `addon.xml` on every change meant to be tested live (convention: `3.23.1.N`).
- Copy touched files into the installed addon directory (same `id`, so Kodi treats it as an in-place
  update without losing addon settings). Kodi does not need restarting — every subtitle search spawns
  `main.py` as a fresh process, so it always picks up the latest files on disk.
- Debug via Kodi's log (`kodi.log` / `kodi.old.log` for the previous run), filtering for `a4ksubtitles`.

## Architecture

### Entry points

- `main.py` (`xbmc.subtitle.module`) — invoked per search/download action; parses the query string
  into `params`, dispatches to `core.main`, always calls `xbmcplugin.endOfDirectory` at the end.
- `main_service.py` (`xbmc.service`) — long-running background loop (`service.py`) that watches
  playback state and triggers auto-search/auto-download/AI-translation without user interaction.
- `a4kSubtitles/api.py` (`A4kSubtitlesApi`) — a parallel entry point used by tests (and any host that
  isn't Kodi itself): drives `core.search`/`core.download` directly, with settings/video-meta mocking
  and `kodi_mock` swapped in for the real `xbmc*` modules. This is what makes the test suite runnable
  outside Kodi.

### The `core` module-as-namespace pattern

`a4kSubtitles/core.py` imports all `lib/*` modules and every feature module (`search`, `download`,
`services`, `data`), then does `utils.core = core` and stores mutable request-scoped state directly as
module attributes (`core.handle`, `core.progress_dialog`, `core.last_meta`, `core.api_mode_enabled`).
Every other module receives `core` as its first argument and reaches everything (`core.kodi`,
`core.logger`, `core.video`, `core.services[name]`, ...) off of it rather than importing directly.
When adding a new helper module, wire it onto `core` the same way rather than importing it standalone
elsewhere — code throughout the codebase assumes `core.<module>` is always reachable.

### Kodi abstraction (`lib/kodi.py` / `lib/kodi_mock.py`)

`lib/kodi.py` decides at import time, via the `A4KSUBTITLES_API_MODE` env var (a JSON blob set by
`api.py`), whether to import real `xbmc*` modules or `kodi_mock` stand-ins per-module. This is what
lets the same production code run both inside real Kodi and in the test suite/CI.

### Search pipeline (`search.py`)

1. `video.get_meta()` builds `meta` from Kodi's now-playing info (title/tvshow/season/episode/imdb_id/
   filehash), scraping/resolving a real IMDB id if Kodi's own metadata is missing or looks wrong
   (`__scrape_imdb_id`, `__update_info_from_imdb`, both cached to disk via `lib/cache.py`).
2. If this is a manual search, `__apply_manual_search_query` overrides that meta: a real IMDB id
   (`^tt\d{7,}$`) resolves fresh metadata via `video.apply_manual_imdb_id`; anything else overwrites
   `meta.title`/`meta.tvshow` as free-text query, deliberately leaving `is_tvshow`/`season`/`episode`
   untouched so TV/anime episode matching still works.
3. The search only fully aborts if there's neither an IMDB id nor a title/tvshow to search with —
   several providers (OpenSubtitles, Podnadpisi, SubDL) can search by plain text and shouldn't be
   blocked just because IMDB matching failed.
4. Each enabled service gets an optional auth thread chained into a search thread
   (`__chain_auth_and_search_threads`), and all such thread pairs are joined with a **15s timeout**
   (`__wait_threads` → `utils.wait_threads(..., timeout=15)`) so one slow/misbehaving provider
   (BSPlayer's polling loop is the known offender) can't block the whole result list from ever
   reaching Kodi. A thread still alive past the timeout is logged and abandoned, not retried.
5. `wait_all_results` (run on its own thread, racing a cancellation-watcher thread against the Kodi
   progress dialog) wraps result assembly in try/except so an unexpected exception surfaces in the
   log and still returns whatever results exist, instead of hanging the dialog forever.
6. `__prepare_results` does the heavy lifting after raw results are in: language filter, dedup by
   URL, then a large heuristic sort (release group/quality/codec/service/audio/color tag matches,
   filename similarity, season/episode match, rating, sync flag) before `__apply_limit` caps results
   per language against `general.results_limit`.
7. Successful result sets are cached to disk (`cache.results_filepath`) keyed by a meta hash, and
   reused on the next identical search unless BSPlayer's cached results have expired (>3 min old),
   in which case just that provider is force-re-searched.

### Service plugin contract (`services/`)

`services/__init__.py` auto-discovers every non-private `.py` file under `services/` and requires it
to define `build_search_requests`, `parse_search_response`, and `build_download_request`;
`build_auth_request`/`parse_auth_response` are optional (defaulted to no-ops when absent). Adding a
new provider means dropping a new module in `services/` implementing that contract — no registration
step elsewhere. `request.py`'s `execute()` is the shared HTTP layer every service's requests flow
through: it handles retries on 429/403/409/502/503, an alternate TLS adapter for hosts needing a
lower cipher security level, and optional Cloudflare bypass via the vendored `cloudscraper` (see
`lib/third_party/`), plus request chaining via a request dict's `next`/`error` callbacks (used e.g.
by OpenSubtitles to resolve a signed download URL after the initial download POST).

### Download flow (`download.py`)

Fetches the provider's archive/raw file, extracts the right subtitle from a zip/gzip (matching by
episode number when known, via `utils.find_file_in_archive`), then post-processes encoding
(chardet detection, cp1251/koi8-r garbled-cyrillic repair) and strips ad lines
(`utils.cleanup_subtitles`, which matches known service names/URLs/"synced by" credit lines).
