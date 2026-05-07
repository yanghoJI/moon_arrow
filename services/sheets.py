import csv
import io
import time
from typing import TypedDict

import httpx

RANK_REQUIRED_HEADERS = (
    "작대",
    "이름",
    "순위",
    "그룹",
    "덤",
    "합시",
    "총합",
    "1순 합",
    "2순 합",
    "3순 합",
)
ROUND_SHOT_HEADERS = (
    ("1-1", "1-2", "1-3", "1-4", "1-5"),
    ("2-1", "2-2", "2-3", "2-4", "2-5"),
    ("3-1", "3-2", "3-3", "3-4", "3-5"),
)

RANK_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1A6Y1lS0ol4r4r1wro0c9dC4Xi-MkpYrhZ38QRVpvEoM"
    "/gviz/tq?tqx=out:csv&sheet=rank"
)
NOTICE_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1A6Y1lS0ol4r4r1wro0c9dC4Xi-MkpYrhZ38QRVpvEoM"
    "/gviz/tq?tqx=out:csv&sheet=board"
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
    second_round_shots: list
    third_round_shots: list
    first_round_display: str
    second_round_display: str
    third_round_display: str
    is_sit_out: bool


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


def _find_header_index(rows: list, required_headers: tuple[str, ...]) -> int:
    required = set(required_headers)
    for index, row in enumerate(rows):
        headers = {value.strip() for value in row if value.strip()}
        if required.issubset(headers):
            return index
    missing = ", ".join(required_headers)
    raise ValueError(f"필수 헤더 행을 찾을 수 없습니다: {missing}")


def _validate_headers(headers: list, required_headers: tuple[str, ...]) -> None:
    header_set = {header.strip() for header in headers if header.strip()}
    missing = [header for header in required_headers if header not in header_set]
    for round_headers in ROUND_SHOT_HEADERS:
        missing.extend(header for header in round_headers if header not in header_set)
    if missing:
        raise ValueError(f"필수 헤더가 없습니다: {', '.join(missing)}")


def _row_to_dict(headers: list, cols: list) -> dict:
    row = {}
    for index, header in enumerate(headers):
        header = header.strip()
        if not header:
            continue
        row[header] = cols[index].strip() if index < len(cols) else ""
    return row


def _round_values(row: dict, headers: tuple[str, ...]) -> tuple[list[int], str]:
    values = [row.get(header, "").strip() for header in headers]
    if all(value == "" for value in values):
        return [0 for _ in headers], "-"
    if any(value == "0" for value in values):
        return [_safe_int(value) for value in values], "0"
    shots = [_safe_int(value) for value in values]
    return shots, str(sum(shots))


async def _fetch_csv(url: str) -> list:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        res = await client.get(f"{url}&t={int(time.time())}")
        res.raise_for_status()
        if res.text.strip().startswith("<"):
            raise ValueError("CSV 대신 HTML 응답이 왔습니다. (공유/권한 설정 확인 필요)")
        return list(csv.reader(io.StringIO(res.text)))


def _parse_rankings(rows: list) -> list:
    if not rows:
        return []

    header_index = _find_header_index(rows, RANK_REQUIRED_HEADERS)
    headers = rows[header_index]
    _validate_headers(headers, RANK_REQUIRED_HEADERS)

    items = []
    for cols in rows[header_index + 1:]:
        row = _row_to_dict(headers, cols)
        name = row.get("이름", "")
        if not name:
            continue
        first_round_shots, first_round_display = _round_values(row, ROUND_SHOT_HEADERS[0])
        second_round_shots, second_round_display = _round_values(row, ROUND_SHOT_HEADERS[1])
        third_round_shots, third_round_display = _round_values(row, ROUND_SHOT_HEADERS[2])
        items.append(RankItem(
            name=name,
            group=row.get("그룹", ""),
            dum=row.get("덤", ""),
            hap_si=_safe_int(row.get("합시", "")),
            total=_safe_int(row.get("총합", "")),
            first_round_shots=first_round_shots,
            second_round_shots=second_round_shots,
            third_round_shots=third_round_shots,
            first_round_sum=_safe_int(row.get("1순 합", "")),
            second_round_sum=_safe_int(row.get("2순 합", "")),
            third_round_sum=_safe_int(row.get("3순 합", "")),
            first_round_display=first_round_display,
            second_round_display=second_round_display,
            third_round_display=third_round_display,
            is_sit_out=row.get("그룹", "") == "-",
        ))

    items.sort(key=lambda x: (
        -x["total"],
        -x["first_round_sum"],
        -x["second_round_sum"],
        -x["third_round_sum"],
    ) + tuple(-s for s in x["first_round_shots"]))

    return items


def _parse_squads(rows: list) -> list:
    if not rows:
        return []

    header_index = _find_header_index(rows, ("작대", "이름"))
    headers = rows[header_index]

    squads: dict = {}
    for cols in rows[header_index + 1:]:
        row = _row_to_dict(headers, cols)
        squad_num = row.get("작대", "")
        name = row.get("이름", "")
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
    try:
        rows = await _fetch_csv(NOTICE_URL)
    except (httpx.HTTPError, ValueError) as exc:
        print(f"[board] 공지 탭을 사용할 수 없어 비활성화합니다: {exc}")
        return []
    if not rows:
        return []

    items = []
    for cols in rows[3:]:
        while len(cols) <= 3:
            cols.append("")
        body = cols[2].strip()
        if body and cols[3].strip() == "1":
            items.append(NoticeItem(time=cols[1].strip(), body=body))
    return list(reversed(items))
