"""One fake server that acts like all seven services. Each lives under its own URL base."""
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

KEYS = {"sonarr": "k-sonarr", "radarr": "k-radarr", "prowlarr": "k-prowlarr",
        "bazarr": "k-bazarr", "overseerr": "k-overseerr", "jellyfin": "k-jellyfin"}
LOG = []

ROUTES = {
    ("sonarr", "GET", "/api/v3/system/status"): {"version": "4.0.1", "appName": "Sonarr"},
    ("sonarr", "GET", "/api/v3/health"): [{"type": "warning", "message": "Indexers unavailable"}],
    ("sonarr", "GET", "/api/v3/queue"): {"records": [{
        "title": "Show.S01E01", "status": "downloading", "size": 1000, "sizeleft": 250,
        "timeleft": "00:10:00", "trackedDownloadState": "downloading", "downloadClient": "qb",
        "series": {"title": "Show"}, "episode": {"seasonNumber": 1, "episodeNumber": 1}}]},
    ("sonarr", "GET", "/api/v3/series/lookup"): [
        {"title": "Show", "year": 2020, "tvdbId": 111, "status": "continuing"},
        {"title": "Owned Show", "year": 2019, "tvdbId": 112, "id": 7}],
    ("sonarr", "GET", "/api/v3/rootfolder"): [{"path": "/tv"}],
    ("sonarr", "GET", "/api/v3/qualityprofile"): [{"id": 1, "name": "HD-1080p"}],
    ("sonarr", "GET", "/api/v3/config/host"): {"apiKey": "k-sonarr", "port": 8989},
    ("sonarr", "GET", "/api/v3/downloadclient"): [{"name": "qb", "fields": [
        {"name": "host", "value": "nas"}, {"name": "password", "value": "hunter22"}]}],
    ("sonarr", "GET", "/api/v3/calendar"): [{"airDateUtc": "2026-10-06T01:00:00Z", "title": "Pilot",
        "seasonNumber": 1, "episodeNumber": 1, "series": {"title": "Show"}, "hasFile": False}],
    ("sonarr", "DELETE", "/api/v3/series/5"): {},
    ("sonarr", "POST", "/api/v3/series"): {"id": 9},
    ("sonarr", "POST", "/api/v3/command"): {"id": 1},
    ("sonarr", "PUT", "/api/v3/series/5"): {"id": 5},
    ("radarr", "GET", "/api/v3/movie/lookup"): [{"title": "Film", "year": 2021, "tmdbId": 222}],
    ("radarr", "GET", "/api/v3/rootfolder"): [{"path": "/movies"}, {"path": "/movies4k"}],
    ("radarr", "GET", "/api/v3/qualityprofile"): [{"id": 1, "name": "Any"}, {"id": 2, "name": "Ultra-HD"}],
    ("radarr", "POST", "/api/v3/movie"): {"id": 20},
    ("prowlarr", "GET", "/api/v1/system/status"): {"version": "1.30", "instanceName": "Prowlarr"},
    ("prowlarr", "GET", "/api/v1/health"): [],
    ("bazarr", "GET", "/api/system/status"): {"data": {"bazarr_version": "1.5.0"}},
    ("bazarr", "GET", "/api/system/health"): {"data": []},
    ("overseerr", "GET", "/api/v1/status"): {"version": "1.34", "updateAvailable": False},
    ("overseerr", "GET", "/api/v1/request"): {"results": [{"id": 3, "status": 1, "type": "movie",
        "media": {"tmdbId": 222}, "requestedBy": {"displayName": "Kid"}, "createdAt": "2026-10-05"}]},
    ("overseerr", "GET", "/api/v1/search"): {"results": [{"mediaType": "movie", "id": 222,
        "title": "Film", "releaseDate": "2021-01-01"}]},
    ("overseerr", "POST", "/api/v1/request/3/approve"): {"id": 3},
    ("overseerr", "POST", "/api/v1/settings/main"): {},
    ("jellyfin", "GET", "/System/Info"): {"ServerName": "jf", "Version": "10.11.0", "HasPendingRestart": False},
    ("jellyfin", "GET", "/Sessions"): [{"UserName": "dad", "DeviceName": "TV", "Client": "Android TV",
        "NowPlayingItem": {"Name": "Movie", "Type": "Movie"}, "PlayState": {"IsPaused": False}}],
    ("jellyfin", "POST", "/Library/Refresh"): None,
    ("jellyfin", "POST", "/System/Restart"): None,
    ("qbittorrent", "GET", "/api/v2/app/version"): "v5.0.0",
    ("qbittorrent", "GET", "/api/v2/transfer/info"): {"dl_info_speed": 1048576, "up_info_speed": 0,
        "connection_status": "connected"},
    ("qbittorrent", "GET", "/api/v2/torrents/info"): [{"name": "Linux.iso", "state": "downloading",
        "progress": 0.5, "dlspeed": 2097152, "upspeed": 0, "eta": 120, "category": "tv",
        "size": 1073741824, "hash": "abc"}],
    ("qbittorrent", "POST", "/api/v2/torrents/pause"): "",
    ("qbittorrent", "POST", "/api/v2/torrents/delete"): "",
    ("qbittorrent", "POST", "/api/v2/app/setPreferences"): "",
}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, payload, ctype="application/json", headers=None):
        raw = b"" if payload is None else (payload.encode() if isinstance(payload, str)
              else json.dumps(payload).encode())
        if isinstance(payload, str):
            ctype = "text/plain"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def handle_any(self, method):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode() if n else ""
        if u.path == "/_log":
            return self.reply(200, LOG)
        parts = u.path.split("/", 2)
        svc, rest = parts[1], "/" + (parts[2] if len(parts) > 2 else "")
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if svc == "qbittorrent":
            if rest == "/api/v2/auth/login":
                f = {k: v[0] for k, v in parse_qs(body).items()}
                if f.get("username") == "admin" and f.get("password") == "pw":
                    return self.reply(200, "Ok.", headers={"Set-Cookie": "SID=abc; HttpOnly; path=/"})
                return self.reply(200, "Fails.")
            if "SID=abc" not in (self.headers.get("Cookie") or ""):
                return self.reply(403, "Forbidden")
        elif svc in KEYS:
            auth = self.headers.get("X-Api-Key") or self.headers.get("Authorization") or ""
            if KEYS[svc] not in auth:
                return self.reply(401, {"error": "Unauthorized"})
        else:
            return self.reply(404, "no such service")
        key = (svc, method, rest)
        if key not in ROUTES:
            return self.reply(404, {"message": "NotFound"})
        if method != "GET":
            LOG.append({"service": svc, "method": method, "path": rest, "query": q, "body": body})
        self.reply(200 if ROUTES[key] is not None else 204, ROUTES[key])

    def do_GET(self): self.handle_any("GET")
    def do_POST(self): self.handle_any("POST")
    def do_PUT(self): self.handle_any("PUT")
    def do_DELETE(self): self.handle_any("DELETE")


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
