import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services import sheets

cache: dict = {
    "rankings": [],
    "notices": [],
    "squads": [],
    "last_updated": None,
}


async def _refresh_loop():
    while True:
        try:
            cache["rankings"] = await sheets.fetch_rankings()
            cache["notices"] = await sheets.fetch_notices()
            cache["squads"] = await sheets.fetch_squads()
            cache["last_updated"] = datetime.now().strftime("%H:%M:%S")
            print(f"[cache] 갱신 완료: {cache['last_updated']}")
        except Exception as exc:
            print(f"[cache] 갱신 실패: {exc}")
        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_refresh_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/rank", response_class=HTMLResponse)
async def rank(request: Request):
    return templates.TemplateResponse("rank.html", {
        "request": request,
        "rankings": cache["rankings"],
        "last_updated": cache["last_updated"],
    })


@app.get("/board", response_class=HTMLResponse)
async def board(request: Request):
    return templates.TemplateResponse("board.html", {
        "request": request,
        "notices": cache["notices"],
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
    uvicorn.run("main:app", host="0.0.0.0", port=9500, reload=True)
