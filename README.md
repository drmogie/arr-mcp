# Arr MCP

![Version](https://img.shields.io/badge/version-2026.10.20.01-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A small tool that lets Claude read and manage your media stack:

- Sonarr (shows)
- Radarr (movies)
- Prowlarr (indexers)
- Bazarr (subtitles)
- Seerr (requests)
- qBittorrent (downloads)
- Jellyfin (your media server)
- Plex (your other media server)
- Tdarr (video conversion)

It runs on your own computer. Your keys stay on your computer.
Only the services you set up are turned on.

## What Claude can do with it

- Check that every service is alive, with version and health warnings.
- Show the download queue, torrents, and upcoming episodes and movies.
- Search for a show or movie and add it (`arr_add`).
- Show Seerr requests. Approve or decline them.
- Show who is watching on Jellyfin and Plex.
- List Plex libraries with item counts (`plex_libraries`).
- Show what Tdarr is converting, and which files failed (`tdarr_summary`).
- Anything else the apps can do (`arr_call`), for example refresh a library,
  trigger a search, pause a torrent, or change a setting.

## Safety

Every call has a safety level.

- **read**: runs right away.
- **change**: does not run until Claude asks you and sets `confirm`.
- **destructive**: deleting, restarting an app, restoring a backup, host and
  security settings, password changes, qBittorrent web login settings.
  It also needs an exact phrase, like `sonarr DELETE /series/5`.

Other protections:

- Login, key and token paths are blocked. They would put a secret in the chat.
- Keys and passwords are hidden in anything Claude sees. This includes the
  password fields inside download client and indexer settings.
- Keys are never printed and never saved by this tool.

## Set up

### 1. Find your keys

- Sonarr, Radarr, Prowlarr: Settings, General, Security, API Key.
- Bazarr: Settings, General, Security, API Key.
- Seerr: Settings, General, API Key.
- Jellyfin: Dashboard, API Keys, add a key named `Claude`.
- Plex: it has no key page. Use your Plex token (open any item in Plex Web, Get Info, View XML, copy the `X-Plex-Token` from the address bar). Treat it like a password.
- Tdarr: Tools, API Keys, make a key named `Claude`.
- qBittorrent: it has no key. Use your web page user name and password.
  Best: turn on the web page login for a separate user if your version allows it.

**Do not paste keys in a chat.** Put them only in the config file below.
If a key ever lands in a chat, make a new one in that app.

### 2. Add the tool to Claude

Open the Claude desktop app settings and find the MCP servers config file.
Add the block from `claude_desktop_config.example.json`.
Change the addresses and keys. Delete the lines for services you do not use.

An address can include a URL base, like `http://nas:8989/sonarr`.

That file now holds secrets. Do not share it. Do not put it on GitHub.

The example uses `uvx`. It downloads arr-mcp from GitHub. No local copy is needed.
To get a new version later, run `uvx --refresh --from git+https://github.com/drmogie/arr-mcp arr-mcp --help` once, or restart the app.
To pin one release, add `@2026.10.12.01` after the URL.

If you do not have `uvx`, use Python instead:

```
pip install git+https://github.com/drmogie/arr-mcp
```

Then use `"command": "arr-mcp"` and no args.

Restart the Claude desktop app.

### 3. Try it

Ask Claude: "Check my arr stack."

## Settings

- `ARR_<SERVICE>_URL` and `ARR_<SERVICE>_KEY`: see the example file.
  Services are `SONARR`, `RADARR`, `PROWLARR`, `BAZARR`, `SEERR`, `JELLYFIN`, `PLEX`, `TDARR`.
- `ARR_QBITTORRENT_URL`. `ARR_QBITTORRENT_USER` and `ARR_QBITTORRENT_PASS` are optional. Leave them out if qBittorrent skips the login for your network.
- `ARR_VERIFY_TLS=false`: for an https address with a self-signed certificate.
- `ARR_TIMEOUT`: seconds to wait for an answer. Default 30.

## Tools

- `arr_services`: which services are set up.
- `arr_status`: version and health for each service.
- `arr_queue`: Sonarr and Radarr downloads.
- `arr_search`: look up a show or movie.
- `arr_add`: add it. Shows a preview first.
- `arr_calendar`: coming episodes and releases.
- `arr_downloads`: qBittorrent torrents.
- `arr_requests`: Seerr requests.
- `jellyfin_now_playing`: who is watching.
- `plex_now_playing`: who is watching on Plex.
- `plex_libraries`: Plex libraries, folders and item counts.
- `tdarr_summary`: Tdarr nodes, workers, files by state, failed files.
- `arr_call`: any other API call.

## Test it

```
pip install "mcp>=1.2,<2"
python tests/test_server.py
```

The test starts a fake server that acts like all nine services.
It checks every tool and every safety rule.

## Limits

- Tested against a fake server only. Not yet tested on your real apps.
- qBittorrent file uploads (adding a `.torrent` file) are not supported.
  Adding by magnet link or URL works.
- Lidarr and Readarr are not included. They use the same style, so they are
  easy to add later.
- Jellyfin library lists can be big. Use `limit` style options in `params`.

## Credits

Built from the public API docs of each app. This project is not made by
any of them.

## License

MIT. See [LICENSE](LICENSE).
