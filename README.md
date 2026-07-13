<img align="left" width="115px" height="115px" src="icon.png">

# a4kSubtitles
[![Kodi version](https://img.shields.io/badge/kodi%20versions-20--21-blue)](https://kodi.tv/)

### General Status
[![Background Service](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-service.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-service.yml)
[![API](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-api.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-api.yml)
[![Search](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-search.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-search.yml)
[![TVShows](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-tvshow.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-tvshow.yml)

### Providers Status
[![Addic7ed](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-addic7ed.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-addic7ed.yml)
[![BSPlayer](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-bsplayer.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-bsplayer.yml)
[![OpenSubtitles](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-opensubtitles.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-opensubtitles.yml)
[![Podnadpisi.NET](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-podnadpisi.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-podnadpisi.yml)
<!-- [![SubDL](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-subdl.yml/badge.svg)](https://github.com/a4k-openproject/a4kSubtitles/actions/workflows/cron-tests-subdl.yml) -->

## Description

Subtitle addon for KODI with support for multiple subtitle services:
* Addic7ed
* BSPlayer
* OpenSubtitles
* Podnadpisi.NET
* SubDL
* SubSource

## This fork

Personal fork on top of upstream `a4k-openproject/a4kSubtitles`, aimed at
content (mainly anime) that the automatic IMDB-based matching fails on.

Changes vs. upstream:

- **Manual search actually works.** Upstream's `manualsearch` action was a
  stub (`main.py` just showed a "Manual search is not supported" toast).
  It's now wired into the real search flow, so the magnifying-glass/manual
  search button in Kodi's subtitle dialog does something.
- **You can type a plain title, or a real IMDB id.** In the manual search
  box: typing normal text (`naruto`) searches by title/tvshow name directly
  against the providers that support it (OpenSubtitles, SubDL, Subsource
  text search, Podnadpisi). Typing an IMDB id (`tt1234567` - either the
  show's own id or a specific episode's id) resolves real metadata from IMDB
  first, which also unlocks providers that hard-require a genuine IMDB id
  (BSPlayer, SubDL for movies, Subsource's imdb search).
- **No more full search abort when IMDB matching fails.** Upstream aborted
  the *entire* search the instant automatic IMDB lookup came back empty
  (`"missing imdb id!"`), even though several providers don't actually need
  one. Now it only bails out if there's truly nothing to search with (no
  IMDB id, no title, no show name).
- **OpenSubtitles no longer discards results just for lacking an IMDB id.**
  Its result filter compared IMDB ids and dropped everything on a mismatch;
  it now only enforces that check when we actually have a trustworthy IMDB
  id on our side.
- **A slow/misbehaving provider can't hang the whole search.** BSPlayer's
  polling loop was observed blocking the final result list from ever
  reaching Kodi (the dialog just sits there with nothing shown, even though
  other providers already had matches). Thread-joining now has a timeout,
  so stragglers get abandoned instead of blocking everyone else.

Known limitations, not fixed (yet):

- BSPlayer, SubDL (movie branch) and Subsource's IMDB-search path still
  return nothing without a *real* IMDB id - that's inherent to how those
  APIs work, not a bug in this fork.
- Podnadpisi/Podnapisi.NET has been seen returning HTTP 500 on every request
  independent of these changes; likely an upstream API/site issue. Easiest
  workaround for now is disabling that provider in the addon settings.

## Configuration
![configuration](https://media.giphy.com/media/kewuE4BgfOnFin0vEC/source.gif)

## Installation

Steps to install a4kSubtitles:
1. Go to the KODI **File manager**.
2. Click on **Add source**.
3. The path for the source is https://a4k-openproject.github.io/a4kSubtitles/packages/
4. (Optional) Name it **a4kSubtitles-repo**.
5. Head to **Addons**.
6. Select **Install from zip file**.
7. When it asks for the location select **a4kSubtitles-repo** and install `a4kSubtitles-repository.zip`.
8. Go back to **Addons** and select **Install from repository**
9. Select the **a4kSubtitles** menu item

## Preview
![usage](https://media.giphy.com/media/QTmhgEJTpTPTPxByfj/source.gif)

## Contribution

Configure hooks for auto update of `addons.xml`:
```sh
git config core.hooksPath .githooks
```
## License

MIT

## Icon

Logo `quill` by Ramy Wafaa ([RoundIcons](https://roundicons.com))
