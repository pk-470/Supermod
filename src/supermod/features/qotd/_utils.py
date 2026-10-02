import random
from typing import Optional

from supermod.features.qotd._constants import *


def use_count(question: list[str]) -> int:
    """
    Read the used count (column D). Blank, "0" and non-numeric all count as
    unused. get_all_values() only pads rows to the widest row, so column D is
    missing entirely when it is blank throughout (e.g. after clearing it).
    """
    try:
        return int(question[3])
    except (IndexError, ValueError):
        return 0


def qotd_get() -> Optional[list[str]]:
    questions: list[list[str]] = qotd_wks().get_all_values()
    questions = [
        question
        for question in questions
        if len(question) > 2
        and question[2]
        and (question[1] == "N" and use_count(question) == 0 or question[1] == "Y")
    ]
    if not questions:
        return None
    question_full = random.choice(questions)
    return question_full


def mark_as_used(question: list[str]) -> None:
    wks = qotd_wks()
    rows = wks.get_all_values()
    matches = [
        row_no
        for row_no, row in enumerate(rows, start=1)
        if len(row) > 2 and row[2] == question[2]
    ]
    assert matches, f"Question not found in the sheet: {question[2]!r}"
    # Some questions appear more than once, so mark the exact row that was
    # picked (same type, repeatable flag and count), not just the first copy.
    row_no = next((n for n in matches if rows[n - 1] == question), matches[0])
    wks.update_cell(row_no, 4, use_count(rows[row_no - 1]) + 1)
