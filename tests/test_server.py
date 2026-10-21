"""End-to-end test: start a fake server for all services, run the MCP tool over stdio, call every tool."""
import asyncio, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
PORT = 5392
BASE = f"http://127.0.0.1:{PORT}"


async def call(session, name, args=None):
    r = await session.call_tool(name, args or {})
    return "\n".join(c.text for c in r.content if hasattr(c, "text"))


def check(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label + ("" if cond else f"  -> {detail[:400]}"))
    return bool(cond)


def log():
    return json.loads(urllib.request.urlopen(f"{BASE}/_log").read())


async def main():
    mock = subprocess.Popen([sys.executable, str(ROOT / "tests" / "mock_arr.py"), str(PORT)])
    time.sleep(0.8)
    ok = True
    try:
        env = {**os.environ, "PYTHONPATH": str(ROOT),
               "ARR_SONARR_URL": f"{BASE}/sonarr", "ARR_SONARR_KEY": "k-sonarr",
               "ARR_RADARR_URL": f"{BASE}/radarr", "ARR_RADARR_KEY": "k-radarr",
               "ARR_PROWLARR_URL": f"{BASE}/prowlarr", "ARR_PROWLARR_KEY": "k-prowlarr",
               "ARR_BAZARR_URL": f"{BASE}/bazarr", "ARR_BAZARR_KEY": "k-bazarr",
               "ARR_SEERR_URL": f"{BASE}/seerr", "ARR_SEERR_KEY": "k-seerr",
               "ARR_JELLYFIN_URL": f"{BASE}/jellyfin", "ARR_JELLYFIN_KEY": "k-jellyfin",
               "ARR_TDARR_URL": f"{BASE}/tdarr", "ARR_TDARR_KEY": "k-tdarr",
               "ARR_PLEX_URL": f"{BASE}/plex", "ARR_PLEX_KEY": "k-plex",
               "ARR_QBITTORRENT_URL": f"{BASE}/qbittorrent",
               "ARR_QBITTORRENT_USER": "admin", "ARR_QBITTORRENT_PASS": "pw"}
        params = StdioServerParameters(command=sys.executable, args=["-m", "arr_mcp"], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = {t.name for t in (await s.list_tools()).tools}
                ok &= check("tools listed", {"arr_services", "arr_call", "arr_status", "arr_queue",
                            "arr_search", "arr_add", "arr_calendar", "arr_downloads",
                            "arr_requests", "jellyfin_now_playing", "tdarr_summary",
                            "plex_now_playing", "plex_libraries"} <= tools, str(tools))

                out = await call(s, "arr_services")
                ok &= check("services list, no keys", "sonarr" in out and "k-sonarr" not in out and "pw" not in out.replace("password", ""), out)

                out = await call(s, "arr_status")
                ok &= check("status all services", all(x in out for x in ["4.0.1", "1.30", "1.5.0", "1.34", "10.11.0", "v5.0.0", "3.00.00", "1.41.0"]), out)
                ok &= check("status shows health warning", "Indexers unavailable" in out, out)

                out = await call(s, "arr_queue")
                ok &= check("queue", "Show.S01E01" in out and "75.0" in out and "S1E1" in out, out)

                out = await call(s, "arr_search", {"term": "show"})
                ok &= check("search sonarr + in_library", "tvdbId" in out and '"library_id": 7' in out, out)
                out = await call(s, "arr_search", {"term": "film", "service": "radarr"})
                ok &= check("search radarr", "Film" in out and "222" in out, out)
                out = await call(s, "arr_search", {"term": "film", "service": "seerr"})
                ok &= check("search seerr", "Film" in out, out)

                out = await call(s, "arr_calendar")
                ok &= check("calendar", "Pilot" in out, out)
                out = await call(s, "arr_downloads")
                ok &= check("downloads", "Linux.iso" in out and "50.0" in out and "2.0" in out, out)
                out = await call(s, "arr_requests")
                ok &= check("requests", "pending" in out and "Kid" in out, out)
                out = await call(s, "jellyfin_now_playing")
                ok &= check("jellyfin sessions", "dad" in out and "Movie" in out, out)

                # Plex
                out = await call(s, "plex_now_playing")
                ok &= check("plex sessions", "mom" in out and "Show - Pilot" in out and "Roku" in out and '"transcoding": true' in out, out)
                out = await call(s, "plex_libraries")
                ok &= check("plex libraries", "Movies" in out and "4200" in out and "/themedia/Video/Movies" in out, out)
                out = await call(s, "arr_call", {"service": "plex", "path": "/library/sections"})
                ok &= check("plex read runs", "NOT RUN" not in out and "Movies" in out, out)
                out = await call(s, "arr_call", {"service": "plex", "path": "/library/sections/1/refresh"})
                ok &= check("plex refresh needs confirm", "NOT RUN" in out, out)
                out = await call(s, "arr_call", {"service": "plex", "path": "/library/sections/1/refresh", "confirm": True})
                ok &= check("plex refresh runs with confirm", "NOT RUN" not in out and "ERROR" not in out, out)
                out = await call(s, "arr_call", {"service": "plex", "path": "/library/sections/1/emptyTrash", "confirm": True})
                ok &= check("plex empty trash needs phrase", "NOT RUN" in out and "plex GET /library/sections/1/emptyTrash" in out, out)
                out = await call(s, "arr_call", {"service": "plex", "path": "/accounts"})
                ok &= check("plex accounts blocked", "not allowed" in out, out)
                out = await call(s, "arr_services")
                ok &= check("plex token not shown", "k-plex" not in out and "plex" in out, out)

                # Tdarr
                out = await call(s, "tdarr_summary")
                ok &= check("tdarr summary", '"Queued": 2' in out and "C.mkv" in out and "themedia-node" in out and '"failed_count": 1' in out, out)
                n = len(log())
                out = await call(s, "arr_call", {"service": "tdarr", "method": "POST", "path": "/cruddb",
                                                 "body": {"data": {"collection": "FileJSONDB", "mode": "getAll"}}})
                ok &= check("tdarr db read runs without confirm", "NOT RUN" not in out and "A.mkv" in out, out)
                n = len(log())
                out = await call(s, "arr_call", {"service": "tdarr", "method": "POST", "path": "/cruddb",
                                                 "body": {"data": {"collection": "LibrarySettingsJSONDB", "mode": "update", "docID": "x", "obj": {}}}})
                ok &= check("tdarr db update needs confirm", "NOT RUN" in out and len(log()) == n, out)
                out = await call(s, "arr_call", {"service": "tdarr", "method": "POST", "path": "/cruddb", "confirm": True,
                                                 "body": {"data": {"collection": "FileJSONDB", "mode": "removeOne", "docID": "x"}}})
                ok &= check("tdarr db remove needs phrase", "NOT RUN" in out and len(log()) == n, out)

                # Reads through arr_call
                out = await call(s, "arr_call", {"service": "qbittorrent", "path": "/app/version"})
                ok &= check("qbit login + plain text", out.strip() == "v5.0.0", out)
                out = await call(s, "arr_call", {"service": "sonarr", "path": "/api/v3/system/status"})
                ok &= check("api prefix is accepted once", "4.0.1" in out, out)

                # Secrets hidden
                out = await call(s, "arr_call", {"service": "sonarr", "path": "/config/host"})
                ok &= check("apiKey hidden", "k-sonarr" not in out and "***" in out and "8989" in out, out)
                out = await call(s, "arr_call", {"service": "sonarr", "path": "/downloadclient"})
                ok &= check("download client password hidden", "hunter22" not in out and "nas" in out, out)

                # Errors
                out = await call(s, "arr_call", {"service": "sonarr", "path": "/nothing"})
                ok &= check("404 hint", "ERROR" in out and "404" in out, out)
                out = await call(s, "arr_call", {"service": "foo", "path": "/x"})
                ok &= check("unknown service", "ERROR" in out, out)
                out = await call(s, "arr_call", {"service": "sonarr", "path": "/series?x=1"})
                ok &= check("query string refused", "ERROR" in out, out)
                out = await call(s, "arr_call", {"service": "sonarr", "path": "/series", "params": {"apikey": "x"}})
                ok &= check("key param refused", "ERROR" in out, out)

                # Blocked paths
                for svc, p in [("qbittorrent", "/auth/login"), ("jellyfin", "/Users/AuthenticateByName"),
                               ("sonarr", "/initialize.js"), ("seerr", "/auth/local")]:
                    out = await call(s, "arr_call", {"service": svc, "path": p, "method": "POST"})
                    ok &= check(f"blocked {svc} {p}", "not allowed" in out, out)

                # Safety: change needs confirm
                n0 = len(log())
                out = await call(s, "arr_call", {"service": "seerr", "method": "POST", "path": "/request/3/approve"})
                ok &= check("change not run without confirm", "NOT RUN" in out and len(log()) == n0, out)
                out = await call(s, "arr_call", {"service": "seerr", "method": "POST", "path": "/request/3/approve", "confirm": True})
                ok &= check("change runs with confirm", "ERROR" not in out and len(log()) == n0 + 1, out)

                # Safety: destructive needs phrase
                n1 = len(log())
                out = await call(s, "arr_call", {"service": "sonarr", "method": "DELETE", "path": "/series/5", "params": {"deleteFiles": True}})
                ok &= check("delete asks first", "NOT RUN" in out and "sonarr DELETE /series/5" in out, out)
                out = await call(s, "arr_call", {"service": "sonarr", "method": "DELETE", "path": "/series/5", "confirm": True})
                ok &= check("delete refused with confirm only", "NOT RUN" in out and len(log()) == n1, out)
                out = await call(s, "arr_call", {"service": "sonarr", "method": "DELETE", "path": "/series/5", "params": {"deleteFiles": True},
                                                 "confirm": True, "confirm_phrase": "sonarr DELETE /series/5"})
                ok &= check("delete runs with phrase", "ERROR" not in out and len(log()) == n1 + 1 and log()[-1]["query"].get("deleteFiles") == "true", out)

                # Destructive classification
                for args in [
                    {"service": "jellyfin", "method": "POST", "path": "/System/Restart"},
                    {"service": "seerr", "method": "POST", "path": "/settings/main"},
                    {"service": "sonarr", "method": "POST", "path": "/command", "body": {"name": "RestartApplication"}},
                    {"service": "qbittorrent", "method": "POST", "path": "/torrents/delete", "params": {"hashes": "abc", "deleteFiles": True}},
                    {"service": "qbittorrent", "method": "POST", "path": "/app/setPreferences", "params": {"json": json.dumps({"web_ui_port": 9999})}},
                ]:
                    n = len(log())
                    out = await call(s, "arr_call", {**args, "confirm": True})
                    ok &= check(f"destructive {args['service']} {args['path']}", "NOT RUN" in out and len(log()) == n, out)

                # qBittorrent form POST (pause) and a plain command
                out = await call(s, "arr_call", {"service": "qbittorrent", "method": "POST", "path": "/torrents/pause",
                                                 "params": {"hashes": "abc"}, "confirm": True})
                ok &= check("qbit pause sends form", "ERROR" not in out and "hashes=abc" in log()[-1]["body"], out)
                out = await call(s, "arr_call", {"service": "sonarr", "method": "POST", "path": "/command",
                                                 "body": {"name": "RefreshSeries"}, "confirm": True})
                ok &= check("command sends json body", "ERROR" not in out and "RefreshSeries" in log()[-1]["body"], out)
                out = await call(s, "arr_call", {"service": "jellyfin", "method": "POST", "path": "/Library/Refresh", "confirm": True})
                ok &= check("204 handled", out.startswith("OK"), out)

                # arr_add
                n = len(log())
                out = await call(s, "arr_add", {"service": "radarr", "external_id": 222})
                ok &= check("add asks for folder and profile", "root_folders" in out and "Ultra-HD" in out and len(log()) == n, out)
                out = await call(s, "arr_add", {"service": "radarr", "external_id": 222, "root_folder": "/movies", "quality_profile": "Any"})
                ok &= check("add preview, not run", "NOT RUN" in out and "Film" in out and len(log()) == n, out)
                out = await call(s, "arr_add", {"service": "radarr", "external_id": 222, "root_folder": "/movies", "quality_profile": "Any", "confirm": True})
                last = log()[-1]
                sent = json.loads(last["body"]) if last["body"] else {}
                ok &= check("add sends right body", "added" in out and last["path"] == "/api/v3/movie"
                            and sent.get("rootFolderPath") == "/movies" and sent.get("qualityProfileId") == 1
                            and sent["addOptions"]["searchForMovie"] is True and sent.get("tmdbId") == 222, out + str(last))
                out = await call(s, "arr_add", {"service": "sonarr", "external_id": 111, "confirm": True})
                last = log()[-1]
                ok &= check("add show uses single defaults", "added" in out and json.loads(last["body"])["rootFolderPath"] == "/tv", out)
    finally:
        mock.terminate()
    print("\nALL PASSED" if ok else "\nSOME FAILED")
    sys.exit(0 if ok else 1)


asyncio.run(main())
