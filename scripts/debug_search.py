# -*- coding: utf-8 -*-
"""
Dev-only helper to run a real manual/auto search against the live provider APIs,
outside of Kodi, with full debug output (bypasses Kodi's debug.showloginfo gate).

Credentials are read from .env (gitignored) at the repo root:
  OPENSUBTITLES_USERNAME, OPENSUBTITLES_PASSWORD, SUBDL_API_KEY, SUBSOURCE_API_KEY

Examples:
  python3 scripts/debug_search.py --query tt0841699
  python3 scripts/debug_search.py --query naruto --tvshow-name Naruto --season 1 --episode 1
  python3 scripts/debug_search.py --query tt0841699 --providers subdl,opensubtitles
"""

import argparse
import json
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)


def load_dotenv():
    env_path = os.path.join(repo_root, '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


ALL_PROVIDERS = ['opensubtitles', 'bsplayer', 'podnadpisi', 'subdl', 'addic7ed', 'subsource']


def build_settings(enabled_providers):
    settings = {
        'general.timeout': '15',
        'general.results_limit': '20',
    }
    for provider in ALL_PROVIDERS:
        settings['%s.enabled' % provider] = 'true' if provider in enabled_providers else 'false'

    settings['opensubtitles.username'] = os.environ.get('OPENSUBTITLES_USERNAME', '')
    settings['opensubtitles.password'] = os.environ.get('OPENSUBTITLES_PASSWORD', '')
    settings['subdl.apikey'] = os.environ.get('SUBDL_API_KEY', '')
    settings['subsource.apikey'] = os.environ.get('SUBSOURCE_API_KEY', '')
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--query', required=True, help='manual search text or an IMDB id (e.g. tt0841699)')
    parser.add_argument('--languages', default='Spanish,English')
    parser.add_argument('--preferred', default='Spanish')
    parser.add_argument('--providers', default=','.join(ALL_PROVIDERS), help='comma list of providers to enable')

    # Initial (pre-manual-override) "now playing" meta, as Kodi would report it before we
    # apply the manual search query. Useful to reproduce is_tvshow being decided *before*
    # the manual query resolves real tvshow/season/episode info from IMDB.
    parser.add_argument('--title', default='', help='initial VideoPlayer title, as if this looked like a movie')
    parser.add_argument('--tvshow-name', dest='tvshow', default='', help='initial VideoPlayer.TVShowTitle, as if Kodi already knew this was a tv episode')
    parser.add_argument('--season', default='')
    parser.add_argument('--episode', default='')
    parser.add_argument('--year', default='')

    args = parser.parse_args()

    load_dotenv()
    os.environ.setdefault('A4KSUBTITLES_DEBUG', 'true')

    from a4kSubtitles import api

    a4k = api.A4kSubtitlesApi({'kodi': True})

    # Force every core.logger.debug(...) call to print unconditionally - in mock mode,
    # get_kodi_setting('debug.showloginfo') always resolves falsy, so lazily-built debug
    # messages (resolved meta, per-provider requests/results, final result count) are
    # normally swallowed entirely, same as with Kodi debug logging turned off.
    a4k.core.logger.debug = lambda msg: print(msg() if callable(msg) else msg, flush=True)

    enabled_providers = [p.strip() for p in args.providers.split(',') if p.strip()]
    settings = build_settings(enabled_providers)

    video_meta = {
        'title': args.title,
        'tvshow': args.tvshow,
        'season': args.season,
        'episode': args.episode,
        'year': args.year,
        'filename': '%s.mkv' % (args.tvshow or args.title or 'debug'),
        'filesize': '',
        'filehash': '',
    }

    params = {
        'languages': args.languages,
        'preferredlanguage': args.preferred,
        'manual_search_query': args.query,
    }

    print('--- settings (enabled providers: %s) ---' % ', '.join(enabled_providers))
    print('--- video_meta (initial, pre-override) ---')
    print(json.dumps(video_meta, indent=2))
    print('--- running search ---')

    results = a4k.search(params, settings, video_meta)

    print('--- final results (%d) ---' % len(results))
    print(json.dumps(results, indent=2, default=str))


if __name__ == '__main__':
    main()
