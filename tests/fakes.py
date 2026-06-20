"""
Reusable in-memory test doubles for the gspread and discord objects the bot
uses, so tests can exercise feature logic without touching Google Sheets or a
live Discord connection."""

from __future__ import annotations

import re
from typing import Optional
from unittest.mock import AsyncMock, MagicMock


def _to_numeric(value) -> Optional[int]:
    """Mirror gspread Cell.numeric_value for ints (None if not parseable)."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


class FakeCell:
    """Stand-in for gspread.cell.Cell."""

    def __init__(self, value="", row: int = 1, col: int = 1):
        self.value = value
        self.row = row
        self.col = col
        self.numeric_value = _to_numeric(value)

    def __repr__(self) -> str:
        return f"FakeCell({self.value!r}, row={self.row}, col={self.col})"


_A1_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def _a1_to_rowcol(a1: str) -> tuple[int, int]:
    """Convert an A1 reference (e.g. 'B3') to 1-based (row, col)."""
    match = _A1_RE.match(a1.strip())
    if not match:
        raise ValueError(f"Bad A1 notation: {a1!r}")
    letters, digits = match.groups()
    col = 0
    for ch in letters.upper():
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return int(digits), col


class FakeWorksheet:
    """
    In-memory stand-in for a gspread Worksheet and Spreadsheet, so one object
    can back either role. Cell access is 1-based and the grid auto-grows on
    write."""

    def __init__(self, rows: Optional[list[list[str]]] = None, title: str = "Sheet1"):
        self.rows: list[list[str]] = [list(r) for r in (rows or [])]
        self.title = title
        # Named child worksheets, addressable by title or index.
        self._worksheets: dict[str, "FakeWorksheet"] = {}

    # --- grid helpers -----------------------------------------------------

    def _ensure(self, row: int, col: int) -> None:
        while len(self.rows) < row:
            self.rows.append([])
        target = self.rows[row - 1]
        while len(target) < col:
            target.append("")

    # --- read -------------------------------------------------------------

    def get_all_values(self) -> list[list[str]]:
        return [list(r) for r in self.rows]

    def row_values(self, row: int) -> list[str]:
        if 1 <= row <= len(self.rows):
            return list(self.rows[row - 1])
        return []

    def cell(self, row: int, col: int) -> FakeCell:
        value = ""
        if 1 <= row <= len(self.rows) and 1 <= col <= len(self.rows[row - 1]):
            value = self.rows[row - 1][col - 1]
        return FakeCell(value, row=row, col=col)

    def acell(self, a1: str) -> FakeCell:
        row, col = _a1_to_rowcol(a1)
        return self.cell(row, col)

    def find(self, query) -> Optional[FakeCell]:
        for r, row in enumerate(self.rows, start=1):
            for c, value in enumerate(row, start=1):
                if value == query:
                    return FakeCell(value, row=r, col=c)
        return None

    # --- write ------------------------------------------------------------

    def update_cell(self, row: int, col: int, value) -> None:
        self._ensure(row, col)
        self.rows[row - 1][col - 1] = value

    def append_row(self, values) -> None:
        self.rows.append(list(values))

    def delete_rows(self, row: int) -> None:
        if 1 <= row <= len(self.rows):
            del self.rows[row - 1]

    def clear(self) -> None:
        self.rows = []

    # --- spreadsheet-style access ----------------------------------------

    def worksheet(self, title: str) -> "FakeWorksheet":
        if title == self.title or title not in self._worksheets:
            return self._worksheets.get(title, self)
        return self._worksheets[title]

    def add_worksheet(self, title: str, ws: "FakeWorksheet") -> "FakeWorksheet":
        self._worksheets[title] = ws
        return ws

    def get_worksheet(self, index: int) -> "FakeWorksheet":
        return self

    @property
    def sheet1(self) -> "FakeWorksheet":
        return self

    def open_by_url(self, url: str) -> "FakeWorksheet":
        return self


def make_message(content: str = "", author_id: int = 1, author_name: str = "tester"):
    """Lightweight discord.Message double."""
    msg = MagicMock(name="Message")
    msg.content = content
    msg.id = 1234567890
    msg.author = MagicMock(name="Member")
    msg.author.id = author_id
    msg.author.display_name = author_name
    msg.reactions = []
    msg.jump_url = "https://discord.com/channels/0/0/0"
    return msg


def make_ctx():
    """
    Lightweight async-capable command Context double whose ``ctx.send`` records
    every sent payload in ``ctx.sent`` for assertions."""
    ctx = MagicMock(name="Context")
    ctx.sent: list = []
    ctx.author = MagicMock(name="Member")
    ctx.author.id = 1
    ctx.author.display_name = "tester"
    ctx.channel = MagicMock(name="Channel")

    async def _send(*args, **kwargs):
        payload = args[0] if args else kwargs.get("content") or kwargs
        ctx.sent.append(payload)
        return make_message(content=str(payload))

    ctx.send = AsyncMock(side_effect=_send)
    return ctx
