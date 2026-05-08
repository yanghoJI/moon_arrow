import json
import re
from pathlib import Path
from typing import Optional

DEFAULT_SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1A6Y1lS0ol4r4r1wro0c9dC4Xi-MkpYrhZ38QRVpvEoM"
    "/edit?usp=sharing"
)
CONFIG_PATH = Path("sheet_config.json")
SPREADSHEET_ID_PATTERN = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")


def parse_spreadsheet_id(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("구글 시트 주소를 입력하세요.")

    match = SPREADSHEET_ID_PATTERN.search(value)
    if match:
        return match.group(1)

    if re.fullmatch(r"[a-zA-Z0-9_-]{20,}", value):
        return value

    raise ValueError("구글 시트 공유 주소 형식이 올바르지 않습니다.")


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _spreadsheet_url(spreadsheet_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?usp=sharing"


def get_spreadsheet_id() -> str:
    config = _load_config()
    saved_id = config.get("spreadsheet_id", "")
    if saved_id:
        return saved_id
    return parse_spreadsheet_id(DEFAULT_SPREADSHEET_URL)


def get_spreadsheet_url() -> str:
    return _spreadsheet_url(get_spreadsheet_id())


def get_csv_url(sheet_name: str, spreadsheet_id: Optional[str] = None) -> str:
    spreadsheet_id = spreadsheet_id or get_spreadsheet_id()
    return (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    )


def save_spreadsheet_id(spreadsheet_id: str) -> None:
    CONFIG_PATH.write_text(
        json.dumps(
            {
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_url": _spreadsheet_url(spreadsheet_id),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
