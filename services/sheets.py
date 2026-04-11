import csv
import io
import time
from typing import TypedDict

import httpx

RANK_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTqsmOlxzgGxrh91wGE0b92x3x40Ta1ZT2l0yd6rTKq5HsrZSng3qocNXwmypouA5F6H68HV46GPVHJ"
    "/pub?gid=0&single=true&output=csv"
)
NOTICE_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTqsmOlxzgGxrh91wGE0b92x3x40Ta1ZT2l0yd6rTKq5HsrZSng3qocNXwmypouA5F6H68HV46GPVHJ"
    "/pub?gid=651255673&single=true&output=csv"
)


class RankItem(TypedDict):
    name: str
    total: int
    first_round_sum: int
    second_round_sum: int
    third_round_sum: int
    first_round_shots: list


class NoticeItem(TypedDict):
    time: str
    body: str


class SquadItem(TypedDict):
    squad_num: str
    members: list


def _safe_int(value: str) -> int:
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return 0


async def _fetch_csv(url: str) -> list:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        res = await client.get(f"{url}&t={int(time.time())}")
        res.raise_for_status()
        if res.text.strip().startswith("<"):
            raise ValueError("CSV 대신 HTML 응답이 왔습니다. (공유/권한 설정 확인 필요)")
        return list(csv.reader(io.StringIO(res.text)))


def _parse_rankings(rows: list) -> list:
    items = []
    for cols in rows[2:]:
        while len(cols) <= 21:
            cols.append("")
        name = cols[1].strip()
        if not name:
            continue
        items.append(RankItem(
            name=name,
            total=_safe_int(cols[3]),
            first_round_shots=[_safe_int(cols[i]) for i in range(4, 9)],
            first_round_sum=_safe_int(cols[9]),
            second_round_sum=_safe_int(cols[15]),
            third_round_sum=_safe_int(cols[21]),
        ))

    items.sort(key=lambda x: (
        -x["total"],
        -x["first_round_sum"],
        -x["second_round_sum"],
        -x["third_round_sum"],
    ) + tuple(-s for s in x["first_round_shots"]))

    return items


def _parse_squads(rows: list) -> list:
    squads: dict = {}
    for cols in rows[2:]:
        while len(cols) <= 1:
            cols.append("")
        squad_num = cols[0].strip()
        name = cols[1].strip()
        if squad_num and name:
            squads.setdefault(squad_num, []).append(name)

    sorted_keys = sorted(squads, key=lambda k: int(k) if k.isdigit() else 0)
    return [SquadItem(squad_num=k, members=squads[k]) for k in sorted_keys]


async def fetch_rank_sheet() -> tuple:
    """RANK_URL을 한 번만 fetch해서 rankings와 squads를 함께 반환."""
    rows = await _fetch_csv(RANK_URL)
    return _parse_rankings(rows), _parse_squads(rows)


async def fetch_notices() -> list:
    rows = await _fetch_csv(NOTICE_URL)
    items = []
    for cols in rows[3:]:
        while len(cols) <= 3:
            cols.append("")
        body = cols[2].strip()
        if body and cols[3].strip() == "1":
            items.append(NoticeItem(time=cols[1].strip(), body=body))
    return list(reversed(items))
