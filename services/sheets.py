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
    group: str
    dum: str
    hap_si: int
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
        while len(cols) <= 24:
            cols.append("")
        name = cols[1].strip()
        if not name:
            continue
        items.append(RankItem(
            name=name,
            group=cols[3].strip(),
            dum=cols[4].strip(),
            hap_si=_safe_int(cols[5]),
            total=_safe_int(cols[6]),
            first_round_shots=[_safe_int(cols[i]) for i in range(7, 12)],
            first_round_sum=_safe_int(cols[12]),
            second_round_sum=_safe_int(cols[18]),
            third_round_sum=_safe_int(cols[24]),
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


def make_teams(rankings: list, num_teams: int) -> list:
    """합시 기준 스네이크 드래프트로 num_teams개의 팀에 선수를 배분."""
    sorted_players = sorted(rankings, key=lambda x: -x["hap_si"])
    teams = [{"team_num": i + 1, "members": [], "hap_si_total": 0} for i in range(num_teams)]
    for i, player in enumerate(sorted_players):
        round_num = i // num_teams
        pos = i % num_teams
        team_idx = pos if round_num % 2 == 0 else (num_teams - 1 - pos)
        teams[team_idx]["members"].append(player)
        teams[team_idx]["hap_si_total"] += player["hap_si"]
    return teams


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
