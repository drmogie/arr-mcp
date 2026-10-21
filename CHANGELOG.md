# Changelog

## 2026.10.20.01

- Added Plex. Set ARR_PLEX_URL and ARR_PLEX_KEY (a Plex token).
- New tools `plex_now_playing` (who is watching) and `plex_libraries` (libraries, folders, item counts).
- `arr_call` works with `plex`. The token is sent as a header, never in the URL, and is hidden in results.
- Plex does some changes with GET (refresh, analyze, empty trash, prefs). These need confirm like any change. Empty trash and updates are destructive.
- Account and token paths (`/myplex`, `/accounts`, `/security/token`) are blocked.

## 2026.10.12.01

- Added Tdarr (video conversion). Set ARR_TDARR_URL and ARR_TDARR_KEY.
- New tool `tdarr_summary`: nodes, workers, files by state, failed files.
- Tdarr reads its database with POST /cruddb. The read modes (getAll, getById)
  run at once. Other modes need confirm. Remove modes are destructive.
- Tdarr keys (seededApiKey, authSecretKey) are hidden in results.
- The example config now installs from GitHub (`git+https://github.com/drmogie/arr-mcp`) instead of a local folder.

## 2026.10.11.02

- Overseerr is now called Seerr. The service name is `seerr`.
- The old names still work: `overseerr` as a service name, and the
  ARR_OVERSEERR_URL and ARR_OVERSEERR_KEY settings.

## 2026.10.11.01

- qBittorrent works without a user name or password when its web page skips
  the login for your network. Leave USER and PASS empty.

## 2026.10.05.01

- First build.
- Sonarr, Radarr, Prowlarr, Bazarr, Overseerr, qBittorrent and Jellyfin.
- Tools: services, status, queue, search, add, calendar, downloads, requests,
  Jellyfin now playing, and a general call tool.
- Safety levels: read, change, destructive. Secrets hidden. Login paths blocked.
