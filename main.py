import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services import sheets

cache: dict = {
    "rankings": [],
    "notices": [],
    "squads": [],
    "teams": [],
    "num_teams": 0,
    "last_updated": None,
}


async def _refresh_cache():
    (rankings, squads), notices = await asyncio.gather(
        sheets.fetch_rank_sheet(),
        sheets.fetch_notices(),
    )
    cache["rankings"] = rankings
    cache["squads"] = squads
    cache["notices"] = notices
    cache["last_updated"] = datetime.now().strftime("%H:%M:%S")
    print(f"[cache] 갱신 완료: {cache['last_updated']}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _refresh_cache()
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


def _diff(old_cache: dict) -> tuple:
    rank_changes = []
    notice_changes = []
    squad_changes = []

    # 등수 비교
    old_ranks = {r["name"]: r for r in old_cache["rankings"]}
    new_ranks = {r["name"]: r for r in cache["rankings"]}
    for name in new_ranks:
        if name not in old_ranks:
            rank_changes.append({"type": "added", "msg": f"+ 새 참가자: {name}"})
    for name in old_ranks:
        if name not in new_ranks:
            rank_changes.append({"type": "removed", "msg": f"- 참가자 제거: {name}"})
    for name in old_ranks:
        if name in new_ranks:
            o, n = old_ranks[name], new_ranks[name]
            if o["total"] != n["total"]:
                rank_changes.append({"type": "updated",
                    "msg": f"~ {name}: 총합 {o['total']} → {n['total']}"})

    # 공지 비교
    old_notices = {(n["time"], n["body"]) for n in old_cache["notices"]}
    new_notices = {(n["time"], n["body"]) for n in cache["notices"]}
    for time, body in new_notices - old_notices:
        preview = body[:40] + ("..." if len(body) > 40 else "")
        notice_changes.append({"type": "added", "msg": f"+ ({time}) {preview}"})
    for time, body in old_notices - new_notices:
        preview = body[:40] + ("..." if len(body) > 40 else "")
        notice_changes.append({"type": "removed", "msg": f"- ({time}) {preview}"})

    # 작대 비교
    old_squads = {s["squad_num"]: _squad_member_names(s) for s in old_cache["squads"]}
    new_squads = {s["squad_num"]: _squad_member_names(s) for s in cache["squads"]}
    for squad_num in sorted(set(old_squads) | set(new_squads), key=lambda k: int(k) if k.isdigit() else 0):
        added = new_squads.get(squad_num, set()) - old_squads.get(squad_num, set())
        removed = old_squads.get(squad_num, set()) - new_squads.get(squad_num, set())
        for m in sorted(added):
            squad_changes.append({"type": "added", "msg": f"+ 작대 {squad_num}: {m}"})
        for m in sorted(removed):
            squad_changes.append({"type": "removed", "msg": f"- 작대 {squad_num}: {m}"})

    return rank_changes, notice_changes, squad_changes


def _squad_member_names(squad: dict) -> set:
    names = set()
    for member in squad["members"]:
        if isinstance(member, dict):
            names.add(member["name"])
        else:
            names.add(member)
    return names


@app.get("/api/refresh")
async def api_refresh(request: Request):
    old_cache = {
        "rankings": list(cache["rankings"]),
        "notices": list(cache["notices"]),
        "squads": list(cache["squads"]),
    }
    await _refresh_cache()
    rank_changes, notice_changes, squad_changes = _diff(old_cache)
    return templates.TemplateResponse("refresh.html", {
        "request": request,
        "updated_at": cache["last_updated"],
        "rank_changes": rank_changes,
        "notice_changes": notice_changes,
        "squad_changes": squad_changes,
    })


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/rank", response_class=HTMLResponse)
async def rank(request: Request, group: Optional[str] = None):
    groups = sheets.available_groups(cache["rankings"])
    selected_group = group if group in groups else None
    return templates.TemplateResponse("rank.html", {
        "request": request,
        "rankings": sheets.ranked_items(cache["rankings"], selected_group),
        "groups": groups,
        "selected_group": selected_group,
        "last_updated": cache["last_updated"],
    })


@app.get("/board", response_class=HTMLResponse)
async def board(request: Request):
    return templates.TemplateResponse("board.html", {
        "request": request,
        "notices": cache["notices"],
        "last_updated": cache["last_updated"],
    })


@app.get("/api/team/clear")
async def api_team_clear():
    cache["teams"] = []
    cache["num_teams"] = 0
    return RedirectResponse(url="/team", status_code=303)


@app.get("/api/team")
async def api_team(n: int = 2):
    n = max(2, min(n, len(cache["rankings"]) or 2))
    cache["teams"] = sheets.make_teams(cache["rankings"], n)
    cache["num_teams"] = n
    return RedirectResponse(url="/team", status_code=303)


@app.get("/team", response_class=HTMLResponse)
async def team(request: Request):
    return templates.TemplateResponse("team.html", {
        "request": request,
        "teams": cache["teams"],
        "num_teams": cache["num_teams"],
        "last_updated": cache["last_updated"],
    })


@app.get("/squad", response_class=HTMLResponse)
async def squad(request: Request):
    return templates.TemplateResponse("squad.html", {
        "request": request,
        "squads": cache["squads"],
        "last_updated": cache["last_updated"],
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10555, reload=True)
