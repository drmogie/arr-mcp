# Arr MCP - project notes

## 2026-10-05: first build (2026.10.05.01)

- Ask: "Can we make a MCP for arr stack", then "add jellyfin to the stack too".
- Mogie chose: Sonarr, Radarr, Prowlarr, Bazarr, Overseerr, qBittorrent,
  Jellyfin. Full control. Name arr-mcp. Where the apps run: not sure
  (so addresses are plain env vars; nothing assumes the Synology).
- Copied the shape of technitium-mcp: env vars only, read / change /
  destructive tiers, confirm and confirm_phrase.
- Phrase for destructive calls: `<service> <METHOD> <path>`.
- No endpoint catalog (unlike Technitium). One general `arr_call` plus
  helper tools for the common jobs.
- Auth per service: X-Api-Key (Sonarr, Radarr, Prowlarr, Bazarr, Overseerr),
  `Authorization: MediaBrowser Token=` (Jellyfin), login cookie
  (qBittorrent; re-logs in once if the cookie dies).
- API roots added by the tool: /api/v3 (Sonarr, Radarr), /api/v1 (Prowlarr,
  Overseerr), /api (Bazarr), /api/v2 (qBittorrent), none (Jellyfin).
- Blocked on purpose: any path with /auth/, authenticate, initialize.js,
  /quickconnect. GET /config/host would show the app key, so secrets are
  hidden in all output (JSON keys and `fields` entries named password etc).
- Tested with a fake server for all seven services over stdio
  (tests/test_server.py, 42 checks). NOT tested on real apps.
- Lesson kept from technitium-mcp: also test the real launch command
  (`uvx --from <folder> arr-mcp`), not only a pre-installed env.
- Not built: .torrent file upload, Lidarr, Readarr.
